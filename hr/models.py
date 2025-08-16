from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from core.models import BaseModel, Department


class Designation(BaseModel):
    """Job designation/position model"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    level = models.IntegerField(default=1, help_text="Hierarchy level (1=highest)")
    min_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    required_qualifications = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    
    class Meta:
        ordering = ['level', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Employee(BaseModel):
    """Employee model extending User"""
    EMPLOYMENT_TYPES = [
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('temporary', 'Temporary'),
        ('intern', 'Intern'),
        ('consultant', 'Consultant'),
    ]
    
    MARITAL_STATUS = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
        ('resigned', 'Resigned'),
        ('retired', 'Retired'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    nationality = models.CharField(max_length=50, default='Indian')
    
    # Contact Information
    personal_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=15)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    
    # Address
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    
    # Employment Details
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='permanent')
    date_of_joining = models.DateField()
    date_of_leaving = models.DateField(null=True, blank=True)
    probation_period_months = models.IntegerField(default=6)
    confirmation_date = models.DateField(null=True, blank=True)
    notice_period_days = models.IntegerField(default=30)
    
    # Salary and Benefits
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Documents
    pan_number = models.CharField(max_length=10, blank=True)
    aadhar_number = models.CharField(max_length=12, blank=True)
    passport_number = models.CharField(max_length=20, blank=True)
    driving_license = models.CharField(max_length=20, blank=True)
    
    # Bank Details
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=20, blank=True)
    ifsc_code = models.CharField(max_length=11, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        ordering = ['employee_id']
    
    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def years_of_service(self):
        if self.date_of_leaving:
            end_date = self.date_of_leaving
        else:
            end_date = date.today()
        
        years = end_date.year - self.date_of_joining.year
        if (end_date.month, end_date.day) < (self.date_of_joining.month, self.date_of_joining.day):
            years -= 1
        return years
    
    @property
    def is_on_probation(self):
        if self.confirmation_date:
            return False
        probation_end = self.date_of_joining + timedelta(days=self.probation_period_months * 30)
        return date.today() <= probation_end


class Attendance(BaseModel):
    """Employee attendance model"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('late', 'Late'),
        ('early_departure', 'Early Departure'),
        ('on_leave', 'On Leave'),
        ('holiday', 'Holiday'),
        ('weekend', 'Weekend'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    total_hours = models.FloatField(default=0)
    overtime_hours = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    remarks = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['employee', 'date']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} - {self.status}"
    
    def calculate_hours(self):
        """Calculate total and overtime hours"""
        if self.check_in_time and self.check_out_time:
            from datetime import datetime, timedelta
            
            # Convert times to datetime for calculation
            check_in = datetime.combine(self.date, self.check_in_time)
            check_out = datetime.combine(self.date, self.check_out_time)
            
            # Handle next day checkout
            if check_out < check_in:
                check_out += timedelta(days=1)
            
            total_time = check_out - check_in
            self.total_hours = total_time.total_seconds() / 3600
            
            # Calculate overtime (assuming 8 hours standard)
            standard_hours = 8
            if self.total_hours > standard_hours:
                self.overtime_hours = self.total_hours - standard_hours
            else:
                self.overtime_hours = 0
            
            self.save()


class LeaveType(BaseModel):
    """Leave type model"""
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    max_days_per_year = models.IntegerField(default=0)
    carry_forward_allowed = models.BooleanField(default=False)
    max_carry_forward_days = models.IntegerField(default=0)
    encashment_allowed = models.BooleanField(default=False)
    requires_medical_certificate = models.BooleanField(default=False)
    advance_notice_days = models.IntegerField(default=1)
    is_paid = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class LeaveBalance(BaseModel):
    """Employee leave balance model"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.IntegerField()
    opening_balance = models.FloatField(default=0)
    earned_leaves = models.FloatField(default=0)
    used_leaves = models.FloatField(default=0)
    carry_forward = models.FloatField(default=0)
    encashed_leaves = models.FloatField(default=0)
    
    class Meta:
        ordering = ['-year']
        unique_together = ['employee', 'leave_type', 'year']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type.name} - {self.year}"
    
    @property
    def available_balance(self):
        """Calculate available leave balance"""
        return self.opening_balance + self.earned_leaves + self.carry_forward - self.used_leaves - self.encashed_leaves


class LeaveApplication(BaseModel):
    """Leave application model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    application_number = models.CharField(max_length=20, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.FloatField()
    reason = models.TextField()
    contact_during_leave = models.CharField(max_length=100, blank=True)
    medical_certificate = models.FileField(upload_to='leave_certificates/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(default=timezone.now)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-applied_date']
    
    def __str__(self):
        return f"{self.application_number} - {self.employee.employee_id}"
    
    def calculate_days(self):
        """Calculate total leave days"""
        delta = self.end_date - self.start_date
        self.total_days = delta.days + 1
        self.save()
    
    def approve_leave(self, approved_by):
        """Approve leave application"""
        self.status = 'approved'
        self.approved_by = approved_by
        self.approved_date = timezone.now()
        self.save()
        
        # Update leave balance
        leave_balance, created = LeaveBalance.objects.get_or_create(
            employee=self.employee,
            leave_type=self.leave_type,
            year=self.start_date.year
        )
        leave_balance.used_leaves += self.total_days
        leave_balance.save()


class Holiday(BaseModel):
    """Holiday calendar model"""
    HOLIDAY_TYPES = [
        ('national', 'National Holiday'),
        ('regional', 'Regional Holiday'),
        ('company', 'Company Holiday'),
        ('optional', 'Optional Holiday'),
    ]
    
    name = models.CharField(max_length=100)
    date = models.DateField()
    holiday_type = models.CharField(max_length=20, choices=HOLIDAY_TYPES)
    description = models.TextField(blank=True)
    is_optional = models.BooleanField(default=False)
    applicable_locations = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['date']
        unique_together = ['name', 'date']
    
    def __str__(self):
        return f"{self.name} - {self.date}"


class Payroll(BaseModel):
    """Payroll model for salary processing"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processed', 'Processed'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    
    # Earnings
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    incentive = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Deductions
    pf_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pf_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    esi_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    esi_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    professional_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    income_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loan_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Totals
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Processing Details
    working_days = models.IntegerField(default=0)
    present_days = models.IntegerField(default=0)
    leave_days = models.IntegerField(default=0)
    overtime_hours = models.FloatField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-pay_period_end']
        unique_together = ['employee', 'pay_period_start', 'pay_period_end']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.pay_period_start} to {self.pay_period_end}"
    
    def calculate_salary(self):
        """Calculate salary components"""
        # Calculate gross salary
        self.gross_salary = (
            self.basic_salary + self.hra + self.transport_allowance +
            self.medical_allowance + self.special_allowance +
            self.overtime_amount + self.bonus + self.incentive
        )
        
        # Calculate total deductions
        self.total_deductions = (
            self.pf_employee + self.esi_employee + self.professional_tax +
            self.income_tax + self.loan_deduction + self.other_deductions
        )
        
        # Calculate net salary
        self.net_salary = self.gross_salary - self.total_deductions
        
        self.save()
    
    def calculate_attendance_based_salary(self):
        """Calculate salary based on attendance"""
        if self.working_days > 0:
            per_day_salary = self.employee.current_salary / self.working_days
            self.basic_salary = per_day_salary * self.present_days
        
        # Calculate allowances proportionally
        if self.working_days > 0:
            attendance_ratio = self.present_days / self.working_days
            base_hra = self.employee.current_salary * Decimal('0.40')  # 40% HRA
            self.hra = base_hra * Decimal(str(attendance_ratio))
            
            base_transport = Decimal('2000')  # Fixed transport allowance
            self.transport_allowance = base_transport * Decimal(str(attendance_ratio))
        
        self.calculate_salary()


class Training(BaseModel):
    """Training program model"""
    TRAINING_TYPES = [
        ('technical', 'Technical Training'),
        ('safety', 'Safety Training'),
        ('soft_skills', 'Soft Skills'),
        ('compliance', 'Compliance Training'),
        ('orientation', 'Orientation'),
        ('leadership', 'Leadership Development'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    training_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    training_type = models.CharField(max_length=20, choices=TRAINING_TYPES)
    description = models.TextField()
    trainer_name = models.CharField(max_length=100)
    trainer_organization = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    duration_hours = models.IntegerField()
    venue = models.CharField(max_length=200)
    max_participants = models.IntegerField(default=20)
    cost_per_participant = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    objectives = models.TextField(blank=True)
    prerequisites = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.training_id} - {self.name}"
    
    @property
    def enrolled_count(self):
        return self.trainingparticipant_set.filter(status__in=['enrolled', 'completed']).count()
    
    @property
    def completion_rate(self):
        total_enrolled = self.enrolled_count
        if total_enrolled > 0:
            completed = self.trainingparticipant_set.filter(status='completed').count()
            return (completed / total_enrolled) * 100
        return 0


class TrainingParticipant(BaseModel):
    """Training participant model"""
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('attended', 'Attended'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(default=timezone.now)
    attendance_percentage = models.FloatField(default=0)
    assessment_score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    certificate_issued = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-enrollment_date']
        unique_together = ['training', 'employee']
    
    def __str__(self):
        return f"{self.training.name} - {self.employee.employee_id}"


class PerformanceReview(BaseModel):
    """Employee performance review model"""
    REVIEW_TYPES = [
        ('annual', 'Annual Review'),
        ('half_yearly', 'Half Yearly'),
        ('quarterly', 'Quarterly'),
        ('probation', 'Probation Review'),
        ('project', 'Project Review'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('self_assessment', 'Self Assessment'),
        ('manager_review', 'Manager Review'),
        ('hr_review', 'HR Review'),
        ('completed', 'Completed'),
    ]
    
    review_id = models.CharField(max_length=20, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPES)
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    
    # Ratings (1-5 scale)
    technical_skills = models.IntegerField(default=0)
    communication_skills = models.IntegerField(default=0)
    teamwork = models.IntegerField(default=0)
    leadership = models.IntegerField(default=0)
    problem_solving = models.IntegerField(default=0)
    initiative = models.IntegerField(default=0)
    punctuality = models.IntegerField(default=0)
    overall_rating = models.FloatField(default=0)
    
    # Comments
    achievements = models.TextField(blank=True)
    areas_of_improvement = models.TextField(blank=True)
    goals_next_period = models.TextField(blank=True)
    employee_comments = models.TextField(blank=True)
    manager_comments = models.TextField(blank=True)
    hr_comments = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    class Meta:
        ordering = ['-review_period_end']
    
    def __str__(self):
        return f"{self.review_id} - {self.employee.employee_id}"
    
    def calculate_overall_rating(self):
        """Calculate overall rating from individual ratings"""
        ratings = [
            self.technical_skills, self.communication_skills, self.teamwork,
            self.leadership, self.problem_solving, self.initiative, self.punctuality
        ]
        valid_ratings = [r for r in ratings if r > 0]
        if valid_ratings:
            self.overall_rating = sum(valid_ratings) / len(valid_ratings)
            self.save()