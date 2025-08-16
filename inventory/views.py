from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Supplier, MaterialCategory, Material, Warehouse, StockMovement,
    PurchaseOrder, PurchaseOrderLineItem, MaterialReceipt, MaterialReceiptLineItem,
    StockAdjustment, StockAdjustmentLineItem
)
from .serializers import (
    SupplierSerializer, MaterialCategorySerializer, MaterialSerializer,
    WarehouseSerializer, StockMovementSerializer, PurchaseOrderSerializer,
    PurchaseOrderCreateSerializer, MaterialReceiptSerializer, MaterialReceiptCreateSerializer,
    StockAdjustmentSerializer, StockAdjustmentCreateSerializer,
    InventoryDashboardStatsSerializer, InventoryReportSerializer, StockLevelSerializer
)


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet for Supplier management"""
    queryset = Supplier.objects.filter(is_active=True)
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier_type', 'country', 'rating']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    ordering_fields = ['name', 'rating', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def purchase_orders(self, request, pk=None):
        """Get all purchase orders for a specific supplier"""
        supplier = self.get_object()
        orders = PurchaseOrder.objects.filter(supplier=supplier)
        serializer = PurchaseOrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get supplier performance metrics"""
        supplier = self.get_object()
        
        # Calculate performance metrics
        orders = PurchaseOrder.objects.filter(supplier=supplier)
        total_orders = orders.count()
        completed_orders = orders.filter(status='completed').count()
        on_time_deliveries = orders.filter(
            status='completed',
            materialreceipt__receipt_date__lte=F('expected_delivery_date')
        ).count()
        
        total_value = orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        avg_delivery_time = orders.filter(status='completed').aggregate(
            avg_days=Avg('materialreceipt__receipt_date') - Avg('order_date')
        )['avg_days']
        
        performance_data = {
            'supplier_id': supplier.id,
            'supplier_name': supplier.name,
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'completion_rate': (completed_orders / total_orders * 100) if total_orders > 0 else 0,
            'on_time_deliveries': on_time_deliveries,
            'on_time_rate': (on_time_deliveries / completed_orders * 100) if completed_orders > 0 else 0,
            'total_value': total_value,
            'average_delivery_days': avg_delivery_time.days if avg_delivery_time else 0,
            'rating': supplier.rating
        }
        
        return Response(performance_data)
    
    @action(detail=False, methods=['get'])
    def top_suppliers(self, request):
        """Get top suppliers by order value"""
        limit = int(request.query_params.get('limit', 10))
        suppliers = Supplier.objects.filter(is_active=True).annotate(
            total_orders=Count('purchaseorder'),
            total_value=Sum('purchaseorder__total_amount')
        ).order_by('-total_value')[:limit]
        
        data = []
        for supplier in suppliers:
            data.append({
                'id': supplier.id,
                'name': supplier.name,
                'total_orders': supplier.total_orders or 0,
                'total_value': supplier.total_value or 0,
                'rating': supplier.rating
            })
        
        return Response(data)


class MaterialCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Material Category management"""
    queryset = MaterialCategory.objects.filter(is_active=True)
    serializer_class = MaterialCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class MaterialViewSet(viewsets.ModelViewSet):
    """ViewSet for Material management"""
    queryset = Material.objects.filter(is_active=True)
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'material_type']
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'current_stock', 'unit_cost', 'created_at']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get materials with low stock"""
        materials = Material.objects.filter(
            is_active=True,
            current_stock__lte=F('reorder_level')
        )
        serializer = self.get_serializer(materials, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get materials that are out of stock"""
        materials = Material.objects.filter(
            is_active=True,
            current_stock__lte=0
        )
        serializer = self.get_serializer(materials, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reorder_required(self, request):
        """Get materials that require reordering"""
        materials = Material.objects.filter(
            is_active=True,
            current_stock__lte=F('minimum_stock_level')
        )
        serializer = self.get_serializer(materials, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stock_movements(self, request, pk=None):
        """Get stock movements for a specific material"""
        material = self.get_object()
        movements = StockMovement.objects.filter(material=material).order_by('-movement_date')
        serializer = StockMovementSerializer(movements, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """Manually adjust stock for a material"""
        material = self.get_object()
        warehouse_id = request.data.get('warehouse_id')
        adjustment_quantity = request.data.get('adjustment_quantity')
        reason = request.data.get('reason', 'Manual adjustment')
        notes = request.data.get('notes', '')
        
        if not warehouse_id or adjustment_quantity is None:
            return Response(
                {'error': 'warehouse_id and adjustment_quantity are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            return Response(
                {'error': 'Warehouse not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create stock adjustment
        adjustment = StockAdjustment.objects.create(
            adjustment_type='manual',
            adjustment_date=timezone.now().date(),
            reason=reason,
            status='approved',
            notes=notes,
            created_by=request.user
        )
        
        # Create adjustment line item
        StockAdjustmentLineItem.objects.create(
            stock_adjustment=adjustment,
            material=material,
            warehouse=warehouse,
            adjustment_quantity=adjustment_quantity,
            reason=reason,
            notes=notes
        )
        
        # Update material stock
        material.update_stock(adjustment_quantity)
        
        # Create stock movement record
        movement_type = 'in' if float(adjustment_quantity) > 0 else 'out'
        StockMovement.objects.create(
            material=material,
            warehouse=warehouse,
            movement_type=movement_type,
            quantity=abs(float(adjustment_quantity)),
            unit_cost=material.unit_cost,
            reference_type='adjustment',
            reference_id=adjustment.id,
            reference_number=adjustment.adjustment_number,
            movement_date=timezone.now().date(),
            notes=f"Stock adjustment: {reason}",
            created_by=request.user
        )
        
        return Response({
            'message': 'Stock adjusted successfully',
            'new_stock_level': material.current_stock,
            'adjustment_number': adjustment.adjustment_number
        })


class WarehouseViewSet(viewsets.ModelViewSet):
    """ViewSet for Warehouse management"""
    queryset = Warehouse.objects.filter(is_active=True)
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['warehouse_type', 'country']
    search_fields = ['name', 'code', 'address']
    ordering_fields = ['name', 'capacity', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def stock_levels(self, request, pk=None):
        """Get stock levels for all materials in this warehouse"""
        warehouse = self.get_object()
        
        # Get stock movements for this warehouse
        movements = StockMovement.objects.filter(warehouse=warehouse)
        
        # Calculate current stock levels per material
        stock_data = []
        materials = Material.objects.filter(is_active=True)
        
        for material in materials:
            material_movements = movements.filter(material=material)
            
            # Calculate current stock for this material in this warehouse
            stock_in = material_movements.filter(movement_type='in').aggregate(
                total=Sum('quantity')
            )['total'] or Decimal('0')
            
            stock_out = material_movements.filter(movement_type='out').aggregate(
                total=Sum('quantity')
            )['total'] or Decimal('0')
            
            current_stock = stock_in - stock_out
            
            if current_stock > 0:  # Only include materials with stock
                stock_data.append({
                    'material_id': material.id,
                    'material_name': material.name,
                    'material_sku': material.sku,
                    'warehouse_id': warehouse.id,
                    'warehouse_name': warehouse.name,
                    'current_stock': current_stock,
                    'minimum_stock_level': material.minimum_stock_level,
                    'reorder_level': material.reorder_level,
                    'maximum_stock_level': material.maximum_stock_level,
                    'stock_status': material.get_stock_status(),
                    'unit_cost': material.unit_cost,
                    'stock_value': current_stock * material.unit_cost
                })
        
        serializer = StockLevelSerializer(stock_data, many=True)
        return Response(serializer.data)


class StockMovementViewSet(viewsets.ModelViewSet):
    """ViewSet for Stock Movement management"""
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['material', 'warehouse', 'movement_type', 'reference_type']
    search_fields = ['material__name', 'material__sku', 'reference_number', 'notes']
    ordering_fields = ['movement_date', 'created_at']
    ordering = ['-movement_date']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Purchase Order management"""
    queryset = PurchaseOrder.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status', 'priority']
    search_fields = ['order_number', 'reference', 'supplier__name']
    ordering_fields = ['order_date', 'expected_delivery_date', 'total_amount']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseOrderCreateSerializer
        return PurchaseOrderSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a purchase order"""
        order = self.get_object()
        if order.status == 'draft':
            order.status = 'approved'
            order.save()
            return Response({'status': 'Purchase order approved'})
        return Response(
            {'error': 'Purchase order cannot be approved'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send purchase order to supplier"""
        order = self.get_object()
        if order.status == 'approved':
            order.status = 'sent'
            order.save()
            return Response({'status': 'Purchase order sent to supplier'})
        return Response(
            {'error': 'Purchase order must be approved before sending'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a purchase order"""
        order = self.get_object()
        if order.status in ['draft', 'approved', 'sent']:
            order.status = 'cancelled'
            order.save()
            return Response({'status': 'Purchase order cancelled'})
        return Response(
            {'error': 'Purchase order cannot be cancelled'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending purchase orders"""
        orders = self.queryset.filter(status__in=['draft', 'approved', 'sent'])
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue purchase orders"""
        today = timezone.now().date()
        orders = self.queryset.filter(
            expected_delivery_date__lt=today,
            status__in=['sent', 'confirmed']
        )
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class MaterialReceiptViewSet(viewsets.ModelViewSet):
    """ViewSet for Material Receipt management"""
    queryset = MaterialReceipt.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'warehouse', 'status', 'quality_status']
    search_fields = ['receipt_number', 'purchase_order__order_number', 'supplier__name']
    ordering_fields = ['receipt_date', 'created_at']
    ordering = ['-receipt_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MaterialReceiptCreateSerializer
        return MaterialReceiptSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm material receipt and update stock"""
        receipt = self.get_object()
        if receipt.status == 'pending':
            receipt.status = 'confirmed'
            receipt.save()
            
            # Update stock levels and create stock movements
            for line_item in receipt.line_items.all():
                material = line_item.material
                
                # Update material stock
                material.update_stock(line_item.quantity_received)
                
                # Create stock movement record
                StockMovement.objects.create(
                    material=material,
                    warehouse=receipt.warehouse,
                    movement_type='in',
                    quantity=line_item.quantity_received,
                    unit_cost=line_item.unit_price,
                    reference_type='receipt',
                    reference_id=receipt.id,
                    reference_number=receipt.receipt_number,
                    movement_date=receipt.receipt_date,
                    notes=f"Material receipt: {receipt.receipt_number}",
                    created_by=request.user
                )
            
            # Update purchase order status if fully received
            if receipt.purchase_order:
                po = receipt.purchase_order
                # Check if all items are fully received
                all_received = True
                for po_item in po.line_items.all():
                    total_received = MaterialReceiptLineItem.objects.filter(
                        material=po_item.material,
                        material_receipt__purchase_order=po,
                        material_receipt__status='confirmed'
                    ).aggregate(total=Sum('quantity_received'))['total'] or Decimal('0')
                    
                    if total_received < po_item.quantity:
                        all_received = False
                        break
                
                if all_received:
                    po.status = 'completed'
                else:
                    po.status = 'partially_received'
                po.save()
            
            return Response({'status': 'Material receipt confirmed and stock updated'})
        return Response(
            {'error': 'Material receipt cannot be confirmed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending material receipts"""
        receipts = self.queryset.filter(status='pending')
        serializer = self.get_serializer(receipts, many=True)
        return Response(serializer.data)


class StockAdjustmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Stock Adjustment management"""
    queryset = StockAdjustment.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['adjustment_type', 'status']
    search_fields = ['adjustment_number', 'reason', 'reference']
    ordering_fields = ['adjustment_date', 'created_at']
    ordering = ['-adjustment_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StockAdjustmentCreateSerializer
        return StockAdjustmentSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve stock adjustment and update stock levels"""
        adjustment = self.get_object()
        if adjustment.status == 'pending':
            adjustment.status = 'approved'
            adjustment.save()
            
            # Apply adjustments to stock levels
            for line_item in adjustment.line_items.all():
                material = line_item.material
                
                # Update material stock
                material.update_stock(line_item.adjustment_quantity)
                
                # Create stock movement record
                movement_type = 'in' if line_item.adjustment_quantity > 0 else 'out'
                StockMovement.objects.create(
                    material=material,
                    warehouse=line_item.warehouse,
                    movement_type=movement_type,
                    quantity=abs(line_item.adjustment_quantity),
                    unit_cost=material.unit_cost,
                    reference_type='adjustment',
                    reference_id=adjustment.id,
                    reference_number=adjustment.adjustment_number,
                    movement_date=adjustment.adjustment_date,
                    notes=f"Stock adjustment: {line_item.reason}",
                    created_by=request.user
                )
            
            return Response({'status': 'Stock adjustment approved and applied'})
        return Response(
            {'error': 'Stock adjustment cannot be approved'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending stock adjustments"""
        adjustments = self.queryset.filter(status='pending')
        serializer = self.get_serializer(adjustments, many=True)
        return Response(serializer.data)


class InventoryDashboardView(viewsets.ViewSet):
    """ViewSet for Inventory Dashboard statistics"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get comprehensive inventory dashboard statistics"""
        # Basic counts
        total_materials = Material.objects.filter(is_active=True).count()
        total_suppliers = Supplier.objects.filter(is_active=True).count()
        total_warehouses = Warehouse.objects.filter(is_active=True).count()
        
        # Stock value calculation
        materials = Material.objects.filter(is_active=True)
        total_stock_value = sum(material.get_stock_value() for material in materials)
        
        # Stock status counts
        in_stock_count = materials.filter(current_stock__gt=F('minimum_stock_level')).count()
        low_stock_count = materials.filter(
            current_stock__lte=F('reorder_level'),
            current_stock__gt=0
        ).count()
        out_of_stock_count = materials.filter(current_stock__lte=0).count()
        reorder_required_count = materials.filter(
            current_stock__lte=F('minimum_stock_level')
        ).count()
        
        # Purchase order stats
        pending_purchase_orders = PurchaseOrder.objects.filter(
            status__in=['draft', 'approved', 'sent']
        ).count()
        pending_receipts = MaterialReceipt.objects.filter(status='pending').count()
        
        # Recent movements (last 10)
        recent_movements = list(
            StockMovement.objects.select_related('material', 'warehouse', 'created_by')
            .order_by('-created_at')[:10]
            .values(
                'id', 'material__name', 'material__sku', 'warehouse__name',
                'movement_type', 'quantity', 'movement_date', 'created_by__username'
            )
        )
        
        # Top materials by value
        top_materials_by_value = []
        for material in materials.order_by('-current_stock')[:10]:
            stock_value = material.get_stock_value()
            if stock_value > 0:
                top_materials_by_value.append({
                    'id': material.id,
                    'name': material.name,
                    'sku': material.sku,
                    'current_stock': float(material.current_stock),
                    'unit_cost': float(material.unit_cost),
                    'stock_value': float(stock_value)
                })
        
        # Low stock materials
        low_stock_materials = list(
            materials.filter(current_stock__lte=F('reorder_level'))
            .values(
                'id', 'name', 'sku', 'current_stock', 'reorder_level',
                'minimum_stock_level', 'unit_cost'
            )[:10]
        )
        
        # Monthly movements (last 12 months)
        monthly_movements = []
        today = timezone.now().date()
        
        for i in range(12):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            movements_in = StockMovement.objects.filter(
                movement_type='in',
                movement_date__range=[month_start, month_end]
            ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
            
            movements_out = StockMovement.objects.filter(
                movement_type='out',
                movement_date__range=[month_start, month_end]
            ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
            
            monthly_movements.append({
                'month': month_start.strftime('%Y-%m'),
                'movements_in': float(movements_in),
                'movements_out': float(movements_out),
                'net_movement': float(movements_in - movements_out)
            })
        
        # Supplier performance
        supplier_performance = list(
            Supplier.objects.filter(is_active=True)
            .annotate(
                total_orders=Count('purchaseorder'),
                total_value=Sum('purchaseorder__total_amount'),
                completed_orders=Count(
                    'purchaseorder',
                    filter=Q(purchaseorder__status='completed')
                )
            )
            .order_by('-total_value')[:5]
            .values(
                'id', 'name', 'total_orders', 'total_value',
                'completed_orders', 'rating'
            )
        )
        
        data = {
            'total_materials': total_materials,
            'total_suppliers': total_suppliers,
            'total_warehouses': total_warehouses,
            'total_stock_value': total_stock_value,
            'in_stock_count': in_stock_count,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'reorder_required_count': reorder_required_count,
            'pending_purchase_orders': pending_purchase_orders,
            'pending_receipts': pending_receipts,
            'recent_movements': recent_movements,
            'top_materials_by_value': top_materials_by_value,
            'low_stock_materials': low_stock_materials,
            'monthly_movements': monthly_movements,
            'supplier_performance': supplier_performance
        }
        
        serializer = InventoryDashboardStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reports(self, request):
        """Generate inventory reports"""
        report_type = request.query_params.get('type', 'stock_levels')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
        
        # Get basic statistics
        materials = Material.objects.filter(is_active=True)
        total_materials = materials.count()
        total_stock_value = sum(material.get_stock_value() for material in materials)
        
        movements = StockMovement.objects.filter(
            movement_date__range=[start_date, end_date]
        )
        total_movements = movements.count()
        
        # Generate report data based on type
        materials_data = []
        movements_data = []
        warehouse_data = []
        supplier_data = []
        
        if report_type == 'stock_levels':
            materials_data = list(
                materials.values(
                    'id', 'name', 'sku', 'current_stock', 'minimum_stock_level',
                    'reorder_level', 'unit_cost'
                )
            )
        elif report_type == 'movements':
            movements_data = list(
                movements.select_related('material', 'warehouse')
                .values(
                    'id', 'material__name', 'material__sku', 'warehouse__name',
                    'movement_type', 'quantity', 'unit_cost', 'movement_date'
                )
            )
        
        data = {
            'report_type': report_type,
            'start_date': start_date,
            'end_date': end_date,
            'total_materials': total_materials,
            'total_stock_value': total_stock_value,
            'total_movements': total_movements,
            'materials_data': materials_data,
            'movements_data': movements_data,
            'warehouse_data': warehouse_data,
            'supplier_data': supplier_data
        }
        
        serializer = InventoryReportSerializer(data)
        return Response(serializer.data)