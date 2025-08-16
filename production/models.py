from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel
from inventory.models import Material
from sales.models import SalesOrder


class ProductionLine(BaseModel):
    """Production line/manufacturing unit model"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    capacity_per_hour = models.FloatField(help_text="Production capacity per hour")
    efficiency_percentage = models.FloatField(default=85.0)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=100)
    installation_date = models.DateField(null=True, blank=True)
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    is_operational = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def effective_capacity(self):
        """Calculate effective capacity considering efficiency"""
        return self.capacity_per_hour * (self.efficiency_percentage / 100)
    
    def get_utilization(self, date_from, date_to):
        """Calculate production line utilization for a period"""
        work_orders = WorkOrder.objects.filter(
            production_line=self,
            start_date__gte=date_from,
            end_date__lte=date_to,
            status__in=['in_progress', 'completed']
        )
        
        total_planned_hours = sum(
            (wo.end_date - wo.start_date).total_seconds() / 3600 
            for wo in work_orders if wo.end_date
        )
        
        period_hours = (date_to - date_from).total_seconds() / 3600
        return (total_planned_hours / period_hours * 100) if period_hours > 0 else 0


class Equipment(BaseModel):
    """Equipment/machinery model"""
    EQUIPMENT_TYPES = [
        ('furnace', 'Furnace'),
        ('rolling_mill', 'Rolling Mill'),
        ('cutting_machine', 'Cutting Machine'),
        ('welding_machine', 'Welding Machine'),
        ('crane', 'Crane'),
        ('conveyor', 'Conveyor'),
        ('testing_equipment', 'Testing Equipment'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('operational', 'Operational'),
        ('maintenance', 'Under Maintenance'),
        ('breakdown', 'Breakdown'),
        ('idle', 'Idle'),
        ('retired', 'Retired'),
    ]
    
    equipment_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    equipment_type = models.CharField(max_length=20, choices=EQUIPMENT_TYPES)
    production_line = models.ForeignKey(ProductionLine, on_delete=models.SET_NULL, null=True, blank=True)
    manufacturer = models.CharField(max_length=100)
    model_number = models.CharField(max_length=50)
    serial_number = models.CharField(max_length=50, unique=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='operational')
    location = models.CharField(max_length=100)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    specifications = models.TextField(blank=True)
    maintenance_schedule_days = models.IntegerField(default=30)
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['equipment_id']
    
    def __str__(self):
        return f"{self.equipment_id} - {self.name}"
    
    def calculate_next_maintenance(self):
        """Calculate next maintenance date"""
        if self.last_maintenance_date:
            from datetime import timedelta
            self.next_maintenance_date = self.last_maintenance_date + timedelta(days=self.maintenance_schedule_days)
            self.save()
    
    @property
    def is_due_for_maintenance(self):
        """Check if equipment is due for maintenance"""
        if self.next_maintenance_date:
            return timezone.now().date() >= self.next_maintenance_date
        return False


class ProductionPlan(BaseModel):
    """Production planning model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    plan_number = models.CharField(max_length=20, unique=True)
    plan_name = models.CharField(max_length=200)
    plan_date = models.DateField(default=timezone.now)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    planner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    total_planned_quantity = models.FloatField(default=0)
    total_produced_quantity = models.FloatField(default=0)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-plan_date']
    
    def __str__(self):
        return f"{self.plan_number} - {self.plan_name}"
    
    @property
    def completion_percentage(self):
        """Calculate plan completion percentage"""
        if self.total_planned_quantity > 0:
            return (self.total_produced_quantity / self.total_planned_quantity) * 100
        return 0
    
    def calculate_totals(self):
        """Calculate total planned and produced quantities"""
        work_orders = self.workorder_set.filter(is_active=True)
        self.total_planned_quantity = sum(wo.planned_quantity for wo in work_orders)
        self.total_produced_quantity = sum(wo.produced_quantity for wo in work_orders)
        self.save()


class WorkOrder(BaseModel):
    """Work order model for production jobs"""
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('released', 'Released'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    wo_number = models.CharField(max_length=20, unique=True)
    production_plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, null=True, blank=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='work_orders')
    production_line = models.ForeignKey(ProductionLine, on_delete=models.SET_NULL, null=True)
    planned_quantity = models.FloatField()
    produced_quantity = models.FloatField(default=0)
    rejected_quantity = models.FloatField(default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    shift = models.CharField(max_length=20, choices=[
        ('day', 'Day Shift'),
        ('night', 'Night Shift'),
        ('general', 'General Shift'),
    ], default='day')
    instructions = models.TextField(blank=True)
    quality_requirements = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.wo_number} - {self.product.name}"
    
    @property
    def completion_percentage(self):
        """Calculate work order completion percentage"""
        if self.planned_quantity > 0:
            return (self.produced_quantity / self.planned_quantity) * 100
        return 0
    
    @property
    def yield_percentage(self):
        """Calculate production yield percentage"""
        total_output = self.produced_quantity + self.rejected_quantity
        if total_output > 0:
            return (self.produced_quantity / total_output) * 100
        return 0
    
    @property
    def is_delayed(self):
        """Check if work order is delayed"""
        if self.end_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.end_date
        return False
    
    def calculate_material_requirements(self):
        """Calculate material requirements for this work order"""
        bom_items = BillOfMaterials.objects.filter(product=self.product, is_active=True)
        requirements = []
        
        for bom_item in bom_items:
            required_quantity = bom_item.quantity_required * self.planned_quantity
            requirements.append({
                'material': bom_item.material,
                'required_quantity': required_quantity,
                'available_stock': bom_item.material.current_stock,
                'shortage': max(0, required_quantity - bom_item.material.current_stock)
            })
        
        return requirements


class BillOfMaterials(BaseModel):
    """Bill of Materials (BOM) model"""
    product = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='bom_items')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='used_in_products')
    quantity_required = models.FloatField(help_text="Quantity required per unit of product")
    unit_of_measure = models.CharField(max_length=20)
    wastage_percentage = models.FloatField(default=0, help_text="Expected wastage percentage")
    sequence_number = models.IntegerField(default=1)
    is_critical = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['product', 'sequence_number']
        unique_together = ['product', 'material']
        verbose_name = 'Bill of Materials'
        verbose_name_plural = 'Bills of Materials'
    
    def __str__(self):
        return f"{self.product.name} -> {self.material.name} ({self.quantity_required})"
    
    @property
    def total_required_with_wastage(self):
        """Calculate total required quantity including wastage"""
        return self.quantity_required * (1 + self.wastage_percentage / 100)


class ProductionEntry(BaseModel):
    """Production entry/transaction model"""
    ENTRY_TYPES = [
        ('production', 'Production Output'),
        ('rework', 'Rework'),
        ('scrap', 'Scrap/Rejection'),
        ('material_consumption', 'Material Consumption'),
    ]
    
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE)
    entry_date = models.DateTimeField(default=timezone.now)
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.FloatField()
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    shift = models.CharField(max_length=20, choices=[
        ('day', 'Day Shift'),
        ('night', 'Night Shift'),
        ('general', 'General Shift'),
    ], default='day')
    quality_grade = models.CharField(max_length=20, choices=[
        ('A', 'Grade A'),
        ('B', 'Grade B'),
        ('C', 'Grade C'),
        ('reject', 'Reject'),
    ], blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-entry_date']
        verbose_name_plural = 'Production Entries'
    
    def __str__(self):
        return f"{self.work_order.wo_number} - {self.entry_type} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update work order quantities
        if self.entry_type == 'production':
            if self.quality_grade != 'reject':
                self.work_order.produced_quantity += self.quantity
            else:
                self.work_order.rejected_quantity += self.quantity
            self.work_order.save()
            
            # Update material stock
            self.material.update_stock(
                quantity=self.quantity,
                transaction_type='production_receipt',
                reference=self.work_order.wo_number
            )
        
        elif self.entry_type == 'material_consumption':
            # Reduce material stock
            self.material.update_stock(
                quantity=self.quantity,
                transaction_type='production_issue',
                reference=self.work_order.wo_number
            )


class QualityCheck(BaseModel):
    """Quality check model for production"""
    CHECK_TYPES = [
        ('incoming', 'Incoming Material'),
        ('in_process', 'In-Process'),
        ('final', 'Final Product'),
        ('random', 'Random Sampling'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('conditional', 'Conditional Pass'),
    ]
    
    check_number = models.CharField(max_length=20, unique=True)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    check_type = models.CharField(max_length=20, choices=CHECK_TYPES)
    check_date = models.DateTimeField(default=timezone.now)
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    quantity_checked = models.FloatField()
    quantity_passed = models.FloatField(default=0)
    quantity_failed = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    test_parameters = models.TextField(blank=True, help_text="Test parameters and specifications")
    test_results = models.TextField(blank=True)
    defects_found = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-check_date']
    
    def __str__(self):
        return f"{self.check_number} - {self.material.name}"
    
    @property
    def pass_percentage(self):
        """Calculate quality pass percentage"""
        if self.quantity_checked > 0:
            return (self.quantity_passed / self.quantity_checked) * 100
        return 0


class MaintenanceSchedule(BaseModel):
    """Maintenance schedule model"""
    MAINTENANCE_TYPES = [
        ('preventive', 'Preventive Maintenance'),
        ('corrective', 'Corrective Maintenance'),
        ('breakdown', 'Breakdown Maintenance'),
        ('overhaul', 'Overhaul'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    ]
    
    maintenance_id = models.CharField(max_length=20, unique=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    scheduled_date = models.DateTimeField()
    estimated_duration_hours = models.FloatField()
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    work_performed = models.TextField(blank=True)
    parts_used = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    next_maintenance_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['scheduled_date']
    
    def __str__(self):
        return f"{self.maintenance_id} - {self.equipment.name}"
    
    @property
    def actual_duration_hours(self):
        """Calculate actual maintenance duration"""
        if self.actual_start_date and self.actual_end_date:
            duration = self.actual_end_date - self.actual_start_date
            return duration.total_seconds() / 3600
        return 0
    
    @property
    def is_overdue(self):
        """Check if maintenance is overdue"""
        if self.status == 'scheduled':
            return timezone.now() > self.scheduled_date
        return False


class ProductionReport(BaseModel):
    """Production report model for daily/shift reports"""
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('shift', 'Shift Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
    ]
    
    report_number = models.CharField(max_length=20, unique=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    report_date = models.DateField()
    production_line = models.ForeignKey(ProductionLine, on_delete=models.CASCADE)
    shift = models.CharField(max_length=20, choices=[
        ('day', 'Day Shift'),
        ('night', 'Night Shift'),
        ('general', 'General Shift'),
    ], blank=True)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    planned_production = models.FloatField(default=0)
    actual_production = models.FloatField(default=0)
    rejected_quantity = models.FloatField(default=0)
    downtime_hours = models.FloatField(default=0)
    efficiency_percentage = models.FloatField(default=0)
    quality_percentage = models.FloatField(default=0)
    energy_consumed = models.FloatField(default=0, help_text="Energy consumed in kWh")
    material_consumed = models.TextField(blank=True, help_text="JSON data of materials consumed")
    issues_faced = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-report_date']
    
    def __str__(self):
        return f"{self.report_number} - {self.production_line.name} - {self.report_date}"
    
    def calculate_efficiency(self):
        """Calculate production efficiency"""
        if self.planned_production > 0:
            self.efficiency_percentage = (self.actual_production / self.planned_production) * 100
        
        total_output = self.actual_production + self.rejected_quantity
        if total_output > 0:
            self.quality_percentage = (self.actual_production / total_output) * 100
        
        self.save()