from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from inventory.models import Material
from .models import (
    ProductionLine, Equipment, ProductionPlan, WorkOrder,
    BillOfMaterials, ProductionEntry, QualityCheck,
    MaintenanceSchedule, ProductionReport
)
from .serializers import (
    ProductionLineSerializer, EquipmentSerializer, ProductionPlanSerializer,
    WorkOrderSerializer, WorkOrderCreateSerializer, BillOfMaterialsSerializer,
    ProductionEntrySerializer, QualityCheckSerializer, MaintenanceScheduleSerializer,
    ProductionReportSerializer, ProductionDashboardStatsSerializer,
    ProductionEfficiencySerializer, ProductionCapacitySerializer,
    MaintenanceAnalyticsSerializer, ProductionOptimizationSerializer
)


class ProductionLineViewSet(viewsets.ModelViewSet):
    """ViewSet for managing production lines"""
    queryset = ProductionLine.objects.all()
    serializer_class = ProductionLineSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset
    
    @action(detail=True, methods=['get'])
    def efficiency(self, request, pk=None):
        """Get efficiency metrics for a production line"""
        production_line = self.get_object()
        # Calculate efficiency metrics
        efficiency_data = {
            'utilization_rate': production_line.utilization_rate,
            'current_efficiency': production_line.efficiency,
            'capacity_per_hour': production_line.capacity_per_hour,
        }
        return Response(efficiency_data)
    
    @action(detail=True, methods=['get'])
    def capacity(self, request, pk=None):
        """Get capacity information for a production line"""
        production_line = self.get_object()
        capacity_data = {
            'capacity_per_hour': production_line.capacity_per_hour,
            'current_utilization': production_line.utilization_rate,
            'status': production_line.status,
        }
        return Response(capacity_data)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics for all production lines"""
        stats = {
            'total_lines': ProductionLine.objects.count(),
            'active_lines': ProductionLine.objects.filter(status='active').count(),
            'maintenance_lines': ProductionLine.objects.filter(status='maintenance').count(),
            'avg_efficiency': ProductionLine.objects.aggregate(
                avg_efficiency=Avg('efficiency')
            )['avg_efficiency'] or 0,
        }
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def work_orders(self, request, pk=None):
        """Get all work orders for a specific production line"""
        production_line = self.get_object()
        orders = WorkOrder.objects.filter(production_line=production_line)
        serializer = WorkOrderSerializer(orders, many=True)
        return Response(serializer.data)


class EquipmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing equipment"""
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status', None)
        production_line = self.request.query_params.get('production_line', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if production_line:
            queryset = queryset.filter(production_line=production_line)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def schedule_maintenance(self, request, pk=None):
        """Schedule maintenance for equipment"""
        equipment = self.get_object()
        maintenance_date = request.data.get('maintenance_date')
        maintenance_type = request.data.get('maintenance_type', 'preventive')
        
        if not maintenance_date:
            return Response(
                {'error': 'Maintenance date is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        maintenance = MaintenanceSchedule.objects.create(
            equipment=equipment,
            maintenance_type=maintenance_type,
            scheduled_date=maintenance_date,
            status='scheduled'
        )
        
        return Response({
            'message': 'Maintenance scheduled successfully',
            'maintenance_id': maintenance.id
        })
    
    @action(detail=True, methods=['get'])
    def maintenance_history(self, request, pk=None):
        """Get maintenance history for equipment"""
        equipment = self.get_object()
        maintenance_records = MaintenanceSchedule.objects.filter(
            equipment=equipment
        ).order_by('-scheduled_date')
        
        serializer = MaintenanceScheduleSerializer(maintenance_records, many=True)
        return Response(serializer.data)


class ProductionPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for managing production plans"""
    queryset = ProductionPlan.objects.all()
    serializer_class = ProductionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a production plan"""
        plan = self.get_object()
        plan.status = 'approved'
        plan.approved_by = request.user
        plan.approved_at = timezone.now()
        plan.save()
        
        return Response({'message': 'Production plan approved successfully'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a production plan"""
        plan = self.get_object()
        plan.status = 'rejected'
        plan.save()
        
        return Response({'message': 'Production plan rejected'})


class WorkOrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing work orders"""
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WorkOrderCreateSerializer
        return WorkOrderSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status', None)
        production_line = self.request.query_params.get('production_line', None)
        priority = self.request.query_params.get('priority', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if production_line:
            queryset = queryset.filter(production_line=production_line)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a work order"""
        work_order = self.get_object()
        work_order.status = 'in_progress'
        work_order.actual_start_date = timezone.now()
        work_order.save()
        
        return Response({'message': 'Work order started successfully'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a work order"""
        work_order = self.get_object()
        actual_quantity = request.data.get('actual_quantity')
        
        if actual_quantity:
            work_order.actual_quantity = actual_quantity
        
        work_order.status = 'completed'
        work_order.actual_end_date = timezone.now()
        work_order.save()
        
        return Response({'message': 'Work order completed successfully'})
    
    @action(detail=False, methods=['get'])
    def active_orders(self, request):
        """Get active work orders"""
        orders = self.queryset.filter(status__in=['scheduled', 'in_progress'])
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class BillOfMaterialsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bill of materials"""
    queryset = BillOfMaterials.objects.all()
    serializer_class = BillOfMaterialsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        product = self.request.query_params.get('product', None)
        
        if product:
            queryset = queryset.filter(product=product)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def cost_analysis(self, request, pk=None):
        """Get cost analysis for BOM"""
        bom = self.get_object()
        # This would calculate total material costs
        # Implementation depends on your material cost model
        return Response({
            'bom_id': bom.id,
            'total_material_cost': 0,  # Calculate based on your logic
            'labor_cost': 0,
            'overhead_cost': 0
        })


class ProductionEntryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing production entries"""
    queryset = ProductionEntry.objects.all()
    serializer_class = ProductionEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        work_order = self.request.query_params.get('work_order', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if work_order:
            queryset = queryset.filter(work_order=work_order)
        if date_from:
            queryset = queryset.filter(entry_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(entry_date__lte=date_to)
        
        return queryset.order_by('-entry_date')
    
    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily production summary"""
        date = request.query_params.get('date', timezone.now().date())
        
        entries = self.queryset.filter(entry_date=date)
        total_production = entries.aggregate(
            total=Sum('actual_quantity')
        )['total'] or 0
        
        return Response({
            'date': date,
            'total_production': total_production,
            'entries_count': entries.count()
        })


class QualityCheckViewSet(viewsets.ModelViewSet):
    """ViewSet for managing quality checks"""
    queryset = QualityCheck.objects.all()
    serializer_class = QualityCheckSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        work_order = self.request.query_params.get('work_order', None)
        status_filter = self.request.query_params.get('status', None)
        
        if work_order:
            queryset = queryset.filter(work_order=work_order)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-check_date')
    
    @action(detail=False, methods=['get'])
    def quality_metrics(self, request):
        """Get quality metrics"""
        start_date = request.query_params.get('start_date', timezone.now().date() - timedelta(days=30))
        end_date = request.query_params.get('end_date', timezone.now().date())
        
        checks = self.queryset.filter(
            check_date__range=[start_date, end_date]
        )
        
        total_checks = checks.count()
        passed_checks = checks.filter(status='passed').count()
        quality_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        return Response({
            'period_start': start_date,
            'period_end': end_date,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'quality_rate': quality_rate
        })


class MaintenanceScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing maintenance schedules"""
    queryset = MaintenanceSchedule.objects.all()
    serializer_class = MaintenanceScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        equipment = self.request.query_params.get('equipment', None)
        status_filter = self.request.query_params.get('status', None)
        
        if equipment:
            queryset = queryset.filter(equipment=equipment)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('scheduled_date')
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark maintenance as completed"""
        maintenance = self.get_object()
        maintenance.status = 'completed'
        maintenance.actual_start_time = request.data.get('actual_start_time', timezone.now())
        maintenance.actual_end_time = request.data.get('actual_end_time', timezone.now())
        maintenance.notes = request.data.get('notes', '')
        maintenance.save()
        
        return Response({'message': 'Maintenance completed successfully'})


class ProductionReportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing production reports"""
    queryset = ProductionReport.objects.all()
    serializer_class = ProductionReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        production_line = self.request.query_params.get('production_line', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if production_line:
            queryset = queryset.filter(production_line=production_line)
        if date_from:
            queryset = queryset.filter(report_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(report_date__lte=date_to)
        
        return queryset.order_by('-report_date')


# Dashboard and Analytics Views
class ProductionDashboardView(viewsets.ViewSet):
    """ViewSet for production dashboard analytics"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get production dashboard statistics"""
        today = timezone.now().date()
        
        # Work order statistics
        total_work_orders = WorkOrder.objects.count()
        active_work_orders = WorkOrder.objects.filter(status='in_progress').count()
        completed_work_orders = WorkOrder.objects.filter(status='completed').count()
        
        # Production line statistics
        total_production_lines = ProductionLine.objects.count()
        operational_lines = ProductionLine.objects.filter(status='active').count()
        
        # Equipment statistics
        total_equipment = Equipment.objects.count()
        operational_equipment = Equipment.objects.filter(status='operational').count()
        
        # Maintenance statistics
        pending_maintenance = MaintenanceSchedule.objects.filter(status='scheduled').count()
        overdue_maintenance = MaintenanceSchedule.objects.filter(
            scheduled_date__lt=today,
            status='scheduled'
        ).count()
        
        # Production metrics
        today_production = ProductionEntry.objects.filter(
            entry_date=today
        ).aggregate(total=Sum('actual_quantity'))['total'] or 0
        
        # Quality metrics
        quality_checks_today = QualityCheck.objects.filter(check_date=today)
        passed_checks = quality_checks_today.filter(status='passed').count()
        total_checks = quality_checks_today.count()
        quality_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Efficiency metrics
        avg_efficiency = ProductionLine.objects.aggregate(
            avg_eff=Avg('efficiency')
        )['avg_eff'] or 0
        
        stats_data = {
            'total_work_orders': total_work_orders,
            'active_work_orders': active_work_orders,
            'completed_work_orders': completed_work_orders,
            'total_production_lines': total_production_lines,
            'operational_lines': operational_lines,
            'total_equipment': total_equipment,
            'operational_equipment': operational_equipment,
            'pending_maintenance': pending_maintenance,
            'overdue_maintenance': overdue_maintenance,
            'avg_efficiency': float(avg_efficiency),
            'total_production_today': float(today_production),
            'quality_rate': float(quality_rate)
        }
        
        serializer = ProductionDashboardStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def efficiency_trends(self, request):
        """Get production efficiency trends"""
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        production_lines = ProductionLine.objects.all()
        efficiency_data = []
        
        for line in production_lines:
            entries = ProductionEntry.objects.filter(
                work_order__production_line=line,
                entry_date__range=[start_date, end_date]
            )
            
            if entries.exists():
                avg_efficiency = line.efficiency
                total_planned = entries.aggregate(Sum('planned_quantity'))['planned_quantity__sum'] or 0
                total_actual = entries.aggregate(Sum('actual_quantity'))['actual_quantity__sum'] or 0
                
                efficiency_data.append({
                    'production_line': line.name,
                    'efficiency_percentage': float(avg_efficiency),
                    'planned_quantity': float(total_planned),
                    'actual_quantity': float(total_actual),
                    'date': end_date
                })
        
        serializer = ProductionEfficiencySerializer(efficiency_data, many=True)
        return Response(serializer.data)