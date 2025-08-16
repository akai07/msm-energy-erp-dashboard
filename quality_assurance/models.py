from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel
from inventory.models import Material, Supplier
from production.models import WorkOrder, ProductionLine
from sales.models import Customer


class QualityStandard(BaseModel):
    """Quality standards and specifications model"""
    STANDARD_TYPES = [
        ('iso', 'ISO Standard'),
        ('astm', 'ASTM Standard'),
        ('din', 'DIN Standard'),
        ('bis', 'BIS Standard'),
        ('internal', 'Internal Standard'),
        ('customer', 'Customer Specification'),
    ]
    
    standard_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    standard_type = models.CharField(max_length=20, choices=STANDARD_TYPES)
    version = models.CharField(max_length=20)
    description = models.TextField()
    applicable_materials = models.ManyToManyField(Material, blank=True)
    test_parameters = models.TextField(help_text="JSON data of test parameters and limits")
    sampling_plan = models.TextField(blank=True)
    acceptance_criteria = models.TextField()
    effective_date = models.DateField()
    review_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['standard_id']
    
    def __str__(self):
        return f"{self.standard_id} - {self.name}"


class TestMethod(BaseModel):
    """Test methods and procedures model"""
    TEST_CATEGORIES = [
        ('chemical', 'Chemical Analysis'),
        ('mechanical', 'Mechanical Testing'),
        ('physical', 'Physical Testing'),
        ('dimensional', 'Dimensional Inspection'),
        ('visual', 'Visual Inspection'),
        ('ndt', 'Non-Destructive Testing'),
    ]
    
    method_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=TEST_CATEGORIES)
    description = models.TextField()
    procedure = models.TextField()
    equipment_required = models.TextField()
    sample_size = models.CharField(max_length=100)
    test_duration_minutes = models.IntegerField(default=30)
    accuracy_level = models.CharField(max_length=50)
    applicable_standards = models.ManyToManyField(QualityStandard, blank=True)
    cost_per_test = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['method_id']
    
    def __str__(self):
        return f"{self.method_id} - {self.name}"


class QualityInspectionPlan(BaseModel):
    """Quality inspection plan model"""
    INSPECTION_TYPES = [
        ('incoming', 'Incoming Material Inspection'),
        ('in_process', 'In-Process Inspection'),
        ('final', 'Final Product Inspection'),
        ('pre_dispatch', 'Pre-Dispatch Inspection'),
    ]
    
    plan_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    inspection_type = models.CharField(max_length=20, choices=INSPECTION_TYPES)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quality_standard = models.ForeignKey(QualityStandard, on_delete=models.CASCADE)
    sampling_percentage = models.FloatField(default=10.0)
    inspection_frequency = models.CharField(max_length=50, help_text="e.g., Every batch, Daily, Weekly")
    test_methods = models.ManyToManyField(TestMethod)
    inspector_required = models.CharField(max_length=100)
    estimated_time_minutes = models.IntegerField(default=60)
    is_mandatory = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['plan_id']
    
    def __str__(self):
        return f"{self.plan_id} - {self.name}"


class QualityInspection(BaseModel):
    """Quality inspection record model"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('conditional', 'Conditional Pass'),
        ('pending', 'Pending'),
    ]
    
    inspection_number = models.CharField(max_length=20, unique=True)
    inspection_plan = models.ForeignKey(QualityInspectionPlan, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    batch_number = models.CharField(max_length=50, blank=True)
    lot_number = models.CharField(max_length=50, blank=True)
    inspection_date = models.DateTimeField(default=timezone.now)
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    quantity_inspected = models.FloatField()
    quantity_accepted = models.FloatField(default=0)
    quantity_rejected = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    overall_result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='pending')
    remarks = models.TextField(blank=True)
    corrective_action_required = models.BooleanField(default=False)
    corrective_action = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-inspection_date']
    
    def __str__(self):
        return f"{self.inspection_number} - {self.material.name}"
    
    @property
    def acceptance_rate(self):
        """Calculate acceptance rate percentage"""
        if self.quantity_inspected > 0:
            return (self.quantity_accepted / self.quantity_inspected) * 100
        return 0
    
    def calculate_result(self):
        """Calculate overall inspection result based on test results"""
        test_results = self.qualitytestresult_set.all()
        if not test_results:
            self.overall_result = 'pending'
        else:
            failed_tests = test_results.filter(result='fail').count()
            if failed_tests > 0:
                self.overall_result = 'fail'
            else:
                conditional_tests = test_results.filter(result='conditional').count()
                if conditional_tests > 0:
                    self.overall_result = 'conditional'
                else:
                    self.overall_result = 'pass'
        self.save()


class QualityTestResult(BaseModel):
    """Individual test result model"""
    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('conditional', 'Conditional'),
        ('not_tested', 'Not Tested'),
    ]
    
    inspection = models.ForeignKey(QualityInspection, on_delete=models.CASCADE)
    test_method = models.ForeignKey(TestMethod, on_delete=models.CASCADE)
    test_parameter = models.CharField(max_length=100)
    specification_min = models.CharField(max_length=50, blank=True)
    specification_max = models.CharField(max_length=50, blank=True)
    actual_value = models.CharField(max_length=50)
    unit_of_measure = models.CharField(max_length=20)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    tested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    test_date = models.DateTimeField(default=timezone.now)
    equipment_used = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['test_method__name']
    
    def __str__(self):
        return f"{self.inspection.inspection_number} - {self.test_parameter}"
    
    def evaluate_result(self):
        """Automatically evaluate test result based on specifications"""
        try:
            actual_float = float(self.actual_value)
            
            if self.specification_min and float(self.specification_min) > actual_float:
                self.result = 'fail'
            elif self.specification_max and float(self.specification_max) < actual_float:
                self.result = 'fail'
            else:
                self.result = 'pass'
        except (ValueError, TypeError):
            # For non-numeric values, manual evaluation required
            self.result = 'not_tested'
        
        self.save()


class NonConformance(BaseModel):
    """Non-conformance report model"""
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('corrective_action', 'Corrective Action in Progress'),
        ('verification', 'Under Verification'),
        ('closed', 'Closed'),
    ]
    
    ncr_number = models.CharField(max_length=20, unique=True)
    inspection = models.ForeignKey(QualityInspection, on_delete=models.CASCADE, null=True, blank=True)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.SET_NULL, null=True, blank=True)
    reported_date = models.DateTimeField(default=timezone.now)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_ncrs')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    quantity_affected = models.FloatField()
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_ncrs')
    target_closure_date = models.DateField(null=True, blank=True)
    actual_closure_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    cost_impact = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_impact = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-reported_date']
        verbose_name = 'Non-Conformance Report'
        verbose_name_plural = 'Non-Conformance Reports'
    
    def __str__(self):
        return f"{self.ncr_number} - {self.material.name}"
    
    @property
    def is_overdue(self):
        """Check if NCR is overdue"""
        if self.target_closure_date and self.status != 'closed':
            return timezone.now().date() > self.target_closure_date
        return False
    
    @property
    def days_open(self):
        """Calculate days since NCR was opened"""
        if self.actual_closure_date:
            return (self.actual_closure_date - self.reported_date.date()).days
        else:
            return (timezone.now().date() - self.reported_date.date()).days


class QualityAlert(BaseModel):
    """Quality alert model for notifications"""
    ALERT_TYPES = [
        ('inspection_due', 'Inspection Due'),
        ('ncr_overdue', 'NCR Overdue'),
        ('quality_trend', 'Quality Trend Alert'),
        ('supplier_quality', 'Supplier Quality Issue'),
        ('customer_complaint', 'Customer Complaint'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    alert_id = models.CharField(max_length=20, unique=True)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    related_material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    related_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    related_ncr = models.ForeignKey(NonConformance, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    due_date = models.DateTimeField(null=True, blank=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    acknowledged_date = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_id} - {self.title}"


class CustomerComplaint(BaseModel):
    """Customer complaint model"""
    COMPLAINT_TYPES = [
        ('quality', 'Quality Issue'),
        ('delivery', 'Delivery Issue'),
        ('packaging', 'Packaging Issue'),
        ('documentation', 'Documentation Issue'),
        ('service', 'Service Issue'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    complaint_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    complaint_type = models.CharField(max_length=20, choices=COMPLAINT_TYPES)
    complaint_date = models.DateTimeField(default=timezone.now)
    description = models.TextField()
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    batch_number = models.CharField(max_length=50, blank=True)
    quantity_affected = models.FloatField(null=True, blank=True)
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    investigation_findings = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    customer_response = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    resolution_date = models.DateTimeField(null=True, blank=True)
    cost_impact = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-complaint_date']
    
    def __str__(self):
        return f"{self.complaint_number} - {self.customer.name}"


class QualityMetrics(BaseModel):
    """Quality metrics and KPI tracking model"""
    METRIC_TYPES = [
        ('defect_rate', 'Defect Rate'),
        ('first_pass_yield', 'First Pass Yield'),
        ('customer_satisfaction', 'Customer Satisfaction'),
        ('supplier_quality', 'Supplier Quality Rating'),
        ('cost_of_quality', 'Cost of Quality'),
        ('inspection_efficiency', 'Inspection Efficiency'),
    ]
    
    PERIOD_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    production_line = models.ForeignKey(ProductionLine, on_delete=models.SET_NULL, null=True, blank=True)
    target_value = models.FloatField()
    actual_value = models.FloatField()
    unit_of_measure = models.CharField(max_length=20)
    variance = models.FloatField(default=0)
    variance_percentage = models.FloatField(default=0)
    trend = models.CharField(max_length=20, choices=[
        ('improving', 'Improving'),
        ('stable', 'Stable'),
        ('declining', 'Declining'),
    ], blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-period_end']
        unique_together = ['metric_type', 'period_start', 'period_end', 'material', 'supplier']
    
    def __str__(self):
        return f"{self.metric_type} - {self.period_start} to {self.period_end}"
    
    def calculate_variance(self):
        """Calculate variance from target"""
        self.variance = self.actual_value - self.target_value
        if self.target_value != 0:
            self.variance_percentage = (self.variance / self.target_value) * 100
        self.save()


class QualityCertificate(BaseModel):
    """Quality certificate model for material/product certification"""
    CERTIFICATE_TYPES = [
        ('material_test', 'Material Test Certificate'),
        ('calibration', 'Calibration Certificate'),
        ('compliance', 'Compliance Certificate'),
        ('iso_certificate', 'ISO Certificate'),
        ('customer_specific', 'Customer Specific Certificate'),
    ]
    
    certificate_number = models.CharField(max_length=30, unique=True)
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=50)
    issue_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    test_results = models.TextField(help_text="JSON data of test results")
    specifications_met = models.TextField()
    remarks = models.TextField(blank=True)
    digital_signature = models.CharField(max_length=500, blank=True)
    is_valid = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.certificate_number} - {self.material.name}"
    
    @property
    def is_expired(self):
        """Check if certificate is expired"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False