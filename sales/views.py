from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Customer, ProductCategory, Product, SalesOrder, SalesOrderLineItem,
    Quotation, QuotationLineItem, Invoice, Payment
)
from .serializers import (
    CustomerSerializer, ProductCategorySerializer, ProductSerializer,
    SalesOrderSerializer, SalesOrderCreateSerializer, QuotationSerializer,
    QuotationCreateSerializer, InvoiceSerializer, PaymentSerializer,
    SalesDashboardStatsSerializer, SalesReportSerializer
)


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for Customer management"""
    queryset = Customer.objects.filter(is_active=True)
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer_type', 'city', 'state', 'country', 'currency']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    ordering_fields = ['name', 'created_at', 'outstanding_balance']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """Get all orders for a specific customer"""
        customer = self.get_object()
        orders = SalesOrder.objects.filter(customer=customer, is_active=True)
        serializer = SalesOrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None):
        """Get all invoices for a specific customer"""
        customer = self.get_object()
        invoices = Invoice.objects.filter(customer=customer, is_active=True)
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Get all payments for a specific customer"""
        customer = self.get_object()
        payments = Payment.objects.filter(customer=customer, is_active=True)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_customers(self, request):
        """Get top customers by revenue"""
        limit = int(request.query_params.get('limit', 10))
        customers = Customer.objects.filter(is_active=True).annotate(
            total_revenue=Sum('salesorder__total_amount')
        ).order_by('-total_revenue')[:limit]
        
        data = []
        for customer in customers:
            data.append({
                'id': customer.id,
                'name': customer.name,
                'total_revenue': customer.total_revenue or 0,
                'outstanding_balance': customer.outstanding_balance
            })
        
        return Response(data)


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Product Category management"""
    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product management"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'product_type', 'track_inventory']
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'unit_price', 'created_at']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def top_selling(self, request):
        """Get top selling products"""
        limit = int(request.query_params.get('limit', 10))
        products = Product.objects.filter(is_active=True).annotate(
            total_sold=Sum('salesorderlineitem__quantity'),
            total_revenue=Sum('salesorderlineitem__line_total')
        ).order_by('-total_sold')[:limit]
        
        data = []
        for product in products:
            data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'total_sold': product.total_sold or 0,
                'total_revenue': product.total_revenue or 0,
                'unit_price': product.unit_price
            })
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock (if inventory tracking is enabled)"""
        # This would need integration with inventory module
        # For now, return products that track inventory
        products = Product.objects.filter(is_active=True, track_inventory=True)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class SalesOrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Sales Order management"""
    queryset = SalesOrder.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'status', 'priority']
    search_fields = ['order_number', 'reference', 'customer__name']
    ordering_fields = ['order_date', 'expected_delivery_date', 'total_amount']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SalesOrderCreateSerializer
        return SalesOrderSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a sales order"""
        order = self.get_object()
        if order.status == 'draft':
            order.status = 'confirmed'
            order.save()
            return Response({'status': 'Order confirmed'})
        return Response(
            {'error': 'Order cannot be confirmed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a sales order"""
        order = self.get_object()
        if order.status in ['draft', 'confirmed']:
            order.status = 'cancelled'
            order.save()
            return Response({'status': 'Order cancelled'})
        return Response(
            {'error': 'Order cannot be cancelled'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def create_invoice(self, request, pk=None):
        """Create invoice from sales order"""
        order = self.get_object()
        if order.status != 'confirmed':
            return Response(
                {'error': 'Order must be confirmed to create invoice'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if invoice already exists
        if Invoice.objects.filter(sales_order=order).exists():
            return Response(
                {'error': 'Invoice already exists for this order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create invoice
        invoice = Invoice.objects.create(
            customer=order.customer,
            sales_order=order,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            created_by=request.user
        )
        
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending sales orders"""
        orders = self.queryset.filter(status__in=['draft', 'confirmed'])
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue sales orders"""
        today = timezone.now().date()
        orders = self.queryset.filter(
            expected_delivery_date__lt=today,
            status__in=['confirmed', 'processing']
        )
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class QuotationViewSet(viewsets.ModelViewSet):
    """ViewSet for Quotation management"""
    queryset = Quotation.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'status']
    search_fields = ['quotation_number', 'reference', 'customer__name']
    ordering_fields = ['quotation_date', 'valid_until', 'total_amount']
    ordering = ['-quotation_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QuotationCreateSerializer
        return QuotationSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a quotation"""
        quotation = self.get_object()
        if quotation.status == 'sent':
            quotation.status = 'accepted'
            quotation.save()
            return Response({'status': 'Quotation accepted'})
        return Response(
            {'error': 'Quotation cannot be accepted'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a quotation"""
        quotation = self.get_object()
        if quotation.status == 'sent':
            quotation.status = 'rejected'
            quotation.save()
            return Response({'status': 'Quotation rejected'})
        return Response(
            {'error': 'Quotation cannot be rejected'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def convert_to_order(self, request, pk=None):
        """Convert quotation to sales order"""
        quotation = self.get_object()
        if quotation.status != 'accepted':
            return Response(
                {'error': 'Quotation must be accepted to convert to order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create sales order from quotation
        order = SalesOrder.objects.create(
            customer=quotation.customer,
            order_date=timezone.now().date(),
            reference=f"From Quotation {quotation.quotation_number}",
            subtotal=quotation.subtotal,
            tax_amount=quotation.tax_amount,
            discount_amount=quotation.discount_amount,
            notes=quotation.notes,
            terms_and_conditions=quotation.terms_and_conditions,
            created_by=request.user
        )
        
        # Copy line items
        for quote_item in quotation.line_items.all():
            SalesOrderLineItem.objects.create(
                sales_order=order,
                product=quote_item.product,
                quantity=quote_item.quantity,
                unit_price=quote_item.unit_price,
                discount_percentage=quote_item.discount_percentage,
                notes=quote_item.notes
            )
        
        order.calculate_total()
        
        # Update quotation status
        quotation.status = 'converted'
        quotation.save()
        
        serializer = SalesOrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get expired quotations"""
        today = timezone.now().date()
        quotations = self.queryset.filter(
            valid_until__lt=today,
            status='sent'
        )
        serializer = self.get_serializer(quotations, many=True)
        return Response(serializer.data)


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Invoice management"""
    queryset = Invoice.objects.filter(is_active=True)
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'status', 'sales_order']
    search_fields = ['invoice_number', 'customer__name']
    ordering_fields = ['invoice_date', 'due_date', 'total_amount']
    ordering = ['-invoice_date']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid"""
        invoice = self.get_object()
        if invoice.status in ['sent', 'overdue']:
            invoice.paid_amount = invoice.total_amount
            invoice.status = 'paid'
            invoice.save()
            return Response({'status': 'Invoice marked as paid'})
        return Response(
            {'error': 'Invoice cannot be marked as paid'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue invoices"""
        today = timezone.now().date()
        invoices = self.queryset.filter(
            due_date__lt=today,
            status__in=['sent', 'overdue']
        )
        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unpaid(self, request):
        """Get unpaid invoices"""
        invoices = self.queryset.filter(status__in=['sent', 'overdue'])
        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment management"""
    queryset = Payment.objects.filter(is_active=True)
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'payment_method', 'status', 'invoice']
    search_fields = ['payment_number', 'transaction_id', 'reference', 'customer__name']
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        payment = serializer.save()
        
        # Update invoice paid amount if payment is confirmed
        if payment.status == 'confirmed' and payment.invoice:
            invoice = payment.invoice
            total_payments = Payment.objects.filter(
                invoice=invoice,
                status='confirmed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            invoice.paid_amount = total_payments
            if invoice.paid_amount >= invoice.total_amount:
                invoice.status = 'paid'
            elif invoice.paid_amount > 0:
                invoice.status = 'partially_paid'
            invoice.save()
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a payment"""
        payment = self.get_object()
        if payment.status == 'pending':
            payment.status = 'confirmed'
            payment.save()
            
            # Update invoice
            if payment.invoice:
                invoice = payment.invoice
                total_payments = Payment.objects.filter(
                    invoice=invoice,
                    status='confirmed'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                invoice.paid_amount = total_payments
                if invoice.paid_amount >= invoice.total_amount:
                    invoice.status = 'paid'
                elif invoice.paid_amount > 0:
                    invoice.status = 'partially_paid'
                invoice.save()
            
            return Response({'status': 'Payment confirmed'})
        return Response(
            {'error': 'Payment cannot be confirmed'},
            status=status.HTTP_400_BAD_REQUEST
        )


class SalesDashboardView(viewsets.ViewSet):
    """ViewSet for Sales Dashboard statistics"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get comprehensive sales dashboard statistics"""
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # Basic stats
        total_customers = Customer.objects.filter(is_active=True).count()
        total_orders = SalesOrder.objects.filter(is_active=True).count()
        total_revenue = SalesOrder.objects.filter(
            is_active=True,
            status__in=['confirmed', 'delivered']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        pending_orders = SalesOrder.objects.filter(
            is_active=True,
            status__in=['draft', 'confirmed']
        ).count()
        
        overdue_invoices = Invoice.objects.filter(
            is_active=True,
            due_date__lt=today,
            status__in=['sent', 'overdue']
        ).count()
        
        total_outstanding = Invoice.objects.filter(
            is_active=True,
            status__in=['sent', 'overdue', 'partially_paid']
        ).aggregate(
            total=Sum('total_amount') - Sum('paid_amount')
        )['total'] or Decimal('0')
        
        # Monthly trends (last 12 months)
        monthly_revenue = []
        monthly_orders = []
        
        for i in range(12):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_revenue = SalesOrder.objects.filter(
                is_active=True,
                order_date__range=[month_start, month_end],
                status__in=['confirmed', 'delivered']
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            
            month_orders = SalesOrder.objects.filter(
                is_active=True,
                order_date__range=[month_start, month_end]
            ).count()
            
            monthly_revenue.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': float(month_revenue)
            })
            
            monthly_orders.append({
                'month': month_start.strftime('%Y-%m'),
                'orders': month_orders
            })
        
        # Top customers
        top_customers = list(Customer.objects.filter(is_active=True).annotate(
            total_revenue=Sum('salesorder__total_amount')
        ).order_by('-total_revenue')[:5].values(
            'id', 'name', 'total_revenue'
        ))
        
        # Top products
        top_products = list(Product.objects.filter(is_active=True).annotate(
            total_sold=Sum('salesorderlineitem__quantity'),
            total_revenue=Sum('salesorderlineitem__line_total')
        ).order_by('-total_revenue')[:5].values(
            'id', 'name', 'sku', 'total_sold', 'total_revenue'
        ))
        
        # Order status distribution
        order_status_distribution = dict(
            SalesOrder.objects.filter(is_active=True).values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
        )
        
        # Payment status distribution
        payment_status_distribution = dict(
            Invoice.objects.filter(is_active=True).values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
        )
        
        data = {
            'total_customers': total_customers,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'pending_orders': pending_orders,
            'overdue_invoices': overdue_invoices,
            'total_outstanding': total_outstanding,
            'monthly_revenue': monthly_revenue,
            'monthly_orders': monthly_orders,
            'top_customers': top_customers,
            'top_products': top_products,
            'order_status_distribution': order_status_distribution,
            'payment_status_distribution': payment_status_distribution
        }
        
        serializer = SalesDashboardStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reports(self, request):
        """Generate sales reports"""
        report_type = request.query_params.get('type', 'monthly')
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
        
        # Get sales data for the period
        orders = SalesOrder.objects.filter(
            is_active=True,
            order_date__range=[start_date, end_date],
            status__in=['confirmed', 'delivered']
        )
        
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        total_orders = orders.count()
        average_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0')
        
        # Sales data by day/week/month based on report type
        sales_data = []
        customer_analysis = []
        product_analysis = []
        
        # This would be expanded based on report_type
        # For now, return basic aggregated data
        
        data = {
            'report_type': report_type,
            'start_date': start_date,
            'end_date': end_date,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'average_order_value': average_order_value,
            'sales_data': sales_data,
            'customer_analysis': customer_analysis,
            'product_analysis': product_analysis
        }
        
        serializer = SalesReportSerializer(data)
        return Response(serializer.data)