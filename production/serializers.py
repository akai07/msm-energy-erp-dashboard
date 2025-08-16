from rest_framework import serializers
from django.contrib.auth.models import User
from inventory.models import Material
from .models import (
    ProductionLine, Equipment, ProductionPlan, WorkOrder,
    BillOfMaterials, ProductionEntry, QualityCheck,
    MaintenanceSchedule, ProductionReport
)


class ProductionLineSerializer(serializers.ModelSerializer):
    """Serializer for ProductionLine model"""
    supervisor_name = serializers.CharField(source='supervisor.username', read_only=True)
    effective_capacity = serializers.FloatField(read_only=True)
    
    class Meta:
        model = ProductionLine
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class EquipmentSerializer(serializers.ModelSerializer):
    """Serializer for Equipment model"""
    production_line_name = serializers.CharField(source='production_line.name', read_only=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    is_due_for_maintenance = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Equipment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class ProductionPlanSerializer(serializers.ModelSerializer):
    """Serializer for ProductionPlan model"""
    planner_name = serializers.CharField(source='planner.username', read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = ProductionPlan
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'completion_percentage')


class WorkOrderSerializer(serializers.ModelSerializer):
    """Serializer for WorkOrder model"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    production_line_name = serializers.CharField(source='production_line.name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.username', read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)
    yield_percentage = serializers.FloatField(read_only=True)
    is_delayed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = WorkOrder
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'completion_percentage', 'yield_percentage', 'is_delayed')


class WorkOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating WorkOrder"""
    
    class Meta:
        model = WorkOrder
        fields = [
            'production_plan', 'sales_order', 'product', 'production_line',
            'planned_quantity', 'start_date', 'end_date', 'priority',
            'supervisor', 'shift', 'instructions', 'quality_requirements'
        ]


class BillOfMaterialsSerializer(serializers.ModelSerializer):
    """Serializer for BillOfMaterials model"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    material_name = serializers.CharField(source='material.name', read_only=True)
    total_required_with_wastage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = BillOfMaterials
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'total_required_with_wastage')


class ProductionEntrySerializer(serializers.ModelSerializer):
    """Serializer for ProductionEntry model"""
    work_order_number = serializers.CharField(source='work_order.wo_number', read_only=True)
    material_name = serializers.CharField(source='material.name', read_only=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    
    class Meta:
        model = ProductionEntry
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class QualityCheckSerializer(serializers.ModelSerializer):
    """Serializer for QualityCheck model"""
    work_order_number = serializers.CharField(source='work_order.wo_number', read_only=True)
    material_name = serializers.CharField(source='material.name', read_only=True)
    inspector_name = serializers.CharField(source='inspector.username', read_only=True)
    pass_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = QualityCheck
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'pass_percentage')


class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    """Serializer for MaintenanceSchedule model"""
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    technician_name = serializers.CharField(source='technician.username', read_only=True)
    actual_duration_hours = serializers.FloatField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MaintenanceSchedule
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'actual_duration_hours', 'is_overdue')


class ProductionReportSerializer(serializers.ModelSerializer):
    """Serializer for ProductionReport model"""
    production_line_name = serializers.CharField(source='production_line.name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.username', read_only=True)
    
    class Meta:
        model = ProductionReport
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


# Dashboard and Analytics Serializers
class ProductionDashboardStatsSerializer(serializers.Serializer):
    """Serializer for production dashboard statistics"""
    total_work_orders = serializers.IntegerField()
    active_work_orders = serializers.IntegerField()
    completed_work_orders = serializers.IntegerField()
    total_production_lines = serializers.IntegerField()
    operational_lines = serializers.IntegerField()
    total_equipment = serializers.IntegerField()
    operational_equipment = serializers.IntegerField()
    pending_maintenance = serializers.IntegerField()
    overdue_maintenance = serializers.IntegerField()
    avg_efficiency = serializers.FloatField()
    total_production_today = serializers.FloatField()
    quality_rate = serializers.FloatField()


class ProductionEfficiencySerializer(serializers.Serializer):
    """Serializer for production efficiency data"""
    production_line = serializers.CharField()
    efficiency_percentage = serializers.FloatField()
    planned_quantity = serializers.FloatField()
    actual_quantity = serializers.FloatField()
    date = serializers.DateField()


class ProductionCapacitySerializer(serializers.Serializer):
    """Serializer for production capacity data"""
    production_line = serializers.CharField()
    capacity_per_hour = serializers.FloatField()
    utilization_rate = serializers.FloatField()
    available_capacity = serializers.FloatField()


class MaintenanceAnalyticsSerializer(serializers.Serializer):
    """Serializer for maintenance analytics"""
    equipment_name = serializers.CharField()
    maintenance_type = serializers.CharField()
    scheduled_date = serializers.DateTimeField()
    status = serializers.CharField()
    cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    duration_hours = serializers.FloatField()


class ProductionOptimizationSerializer(serializers.Serializer):
    """Serializer for production optimization recommendations"""
    production_line = serializers.CharField()
    current_efficiency = serializers.FloatField()
    potential_improvement = serializers.FloatField()
    recommendations = serializers.ListField(child=serializers.CharField())
    priority = serializers.CharField()
    estimated_savings = serializers.DecimalField(max_digits=10, decimal_places=2)