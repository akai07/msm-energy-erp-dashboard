from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from core.models import BaseModel


class AccountType(BaseModel):
    """Chart of Accounts - Account Types"""
    ACCOUNT_CATEGORIES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('REVENUE', 'Revenue'),
        ('EXPENSE', 'Expense'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=ACCOUNT_CATEGORIES)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Account(BaseModel):
    """Chart of Accounts"""
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_bank_account = models.BooleanField(default=False)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def update_balance(self):
        """Update current balance based on transactions"""
        from django.db.models import Sum, Q
        
        debits = JournalEntry.objects.filter(
            account=self, entry_type='DEBIT'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        credits = JournalEntry.objects.filter(
            account=self, entry_type='CREDIT'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if self.account_type.category in ['ASSET', 'EXPENSE']:
            self.current_balance = self.opening_balance + debits - credits
        else:
            self.current_balance = self.opening_balance + credits - debits
        
        self.save()


class Transaction(BaseModel):
    """Financial Transactions"""
    TRANSACTION_TYPES = [
        ('RECEIPT', 'Receipt'),
        ('PAYMENT', 'Payment'),
        ('JOURNAL', 'Journal Entry'),
        ('TRANSFER', 'Transfer'),
    ]
    
    transaction_number = models.CharField(max_length=50, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_posted = models.BooleanField(default=False)
    posted_date = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_transactions')
    
    # Related documents
    invoice = models.ForeignKey('sales.Invoice', on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order = models.ForeignKey('inventory.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.transaction_number} - {self.description}"
    
    def post_transaction(self, user):
        """Post transaction to accounts"""
        if not self.is_posted:
            self.is_posted = True
            self.posted_date = timezone.now()
            self.posted_by = user
            self.save()
            
            # Update account balances
            for entry in self.journal_entries.all():
                entry.account.update_balance()


class JournalEntry(BaseModel):
    """Journal Entries for Double Entry Bookkeeping"""
    ENTRY_TYPES = [
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    ]
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='journal_entries')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['transaction', 'entry_type']
    
    def __str__(self):
        return f"{self.transaction.transaction_number} - {self.account.name} ({self.entry_type})"


class Budget(BaseModel):
    """Budget Planning"""
    BUDGET_TYPES = [
        ('ANNUAL', 'Annual Budget'),
        ('QUARTERLY', 'Quarterly Budget'),
        ('MONTHLY', 'Monthly Budget'),
        ('PROJECT', 'Project Budget'),
    ]
    
    name = models.CharField(max_length=200)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_budget = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
    
    @property
    def allocated_amount(self):
        """Total allocated amount across all line items"""
        return self.budget_lines.aggregate(
            total=models.Sum('allocated_amount')
        )['total'] or 0
    
    @property
    def spent_amount(self):
        """Total spent amount across all line items"""
        return self.budget_lines.aggregate(
            total=models.Sum('spent_amount')
        )['total'] or 0
    
    @property
    def remaining_amount(self):
        """Remaining budget amount"""
        return self.allocated_amount - self.spent_amount
    
    @property
    def utilization_percentage(self):
        """Budget utilization percentage"""
        if self.allocated_amount > 0:
            return (self.spent_amount / self.allocated_amount) * 100
        return 0


class BudgetLineItem(BaseModel):
    """Budget Line Items"""
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='budget_lines')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['budget', 'account']
        ordering = ['account__code']
    
    def __str__(self):
        return f"{self.budget.name} - {self.account.name}"
    
    @property
    def remaining_amount(self):
        """Remaining amount for this line item"""
        return self.allocated_amount - self.spent_amount
    
    @property
    def utilization_percentage(self):
        """Utilization percentage for this line item"""
        if self.allocated_amount > 0:
            return (self.spent_amount / self.allocated_amount) * 100
        return 0
    
    def update_spent_amount(self):
        """Update spent amount based on actual transactions"""
        from django.db.models import Sum
        
        spent = JournalEntry.objects.filter(
            account=self.account,
            transaction__date__range=[self.budget.start_date, self.budget.end_date],
            transaction__is_posted=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        self.spent_amount = spent
        self.save()


class CostCenter(BaseModel):
    """Cost Centers for expense allocation"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class FinancialReport(BaseModel):
    """Financial Reports"""
    REPORT_TYPES = [
        ('BALANCE_SHEET', 'Balance Sheet'),
        ('INCOME_STATEMENT', 'Income Statement'),
        ('CASH_FLOW', 'Cash Flow Statement'),
        ('TRIAL_BALANCE', 'Trial Balance'),
        ('BUDGET_VARIANCE', 'Budget Variance Report'),
        ('COST_CENTER', 'Cost Center Report'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    generated_date = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    report_data = models.JSONField()  # Store report data as JSON
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-generated_date']
    
    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"


class TaxConfiguration(BaseModel):
    """Tax Configuration"""
    TAX_TYPES = [
        ('GST', 'Goods and Services Tax'),
        ('VAT', 'Value Added Tax'),
        ('INCOME_TAX', 'Income Tax'),
        ('CORPORATE_TAX', 'Corporate Tax'),
        ('CUSTOMS_DUTY', 'Customs Duty'),
        ('EXCISE_DUTY', 'Excise Duty'),
    ]
    
    name = models.CharField(max_length=100)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPES)
    rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    description = models.TextField(blank=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['tax_type', '-effective_from']
    
    def __str__(self):
        return f"{self.name} ({self.rate}%)"
    
    def is_active(self, date=None):
        """Check if tax configuration is active on given date"""
        from django.utils import timezone
        
        if date is None:
            date = timezone.now().date()
        
        if date < self.effective_from:
            return False
        
        if self.effective_to and date > self.effective_to:
            return False
        
        return True


class BankReconciliation(BaseModel):
    """Bank Reconciliation"""
    RECONCILIATION_STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('DISCREPANCY', 'Discrepancy Found'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, limit_choices_to={'is_bank_account': True})
    statement_date = models.DateField()
    statement_balance = models.DecimalField(max_digits=15, decimal_places=2)
    book_balance = models.DecimalField(max_digits=15, decimal_places=2)
    reconciled_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=RECONCILIATION_STATUS, default='PENDING')
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reconciled_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-statement_date']
        unique_together = ['account', 'statement_date']
    
    def __str__(self):
        return f"{self.account.name} - {self.statement_date}"
    
    @property
    def difference(self):
        """Difference between statement and book balance"""
        return self.statement_balance - self.book_balance
    
    def mark_completed(self, user):
        """Mark reconciliation as completed"""
        from django.utils import timezone
        
        self.status = 'COMPLETED'
        self.reconciled_by = user
        self.reconciled_date = timezone.now()
        self.save()


class FixedAsset(BaseModel):
    """Fixed Assets Management"""
    ASSET_CATEGORIES = [
        ('BUILDING', 'Building'),
        ('MACHINERY', 'Machinery'),
        ('EQUIPMENT', 'Equipment'),
        ('VEHICLE', 'Vehicle'),
        ('FURNITURE', 'Furniture'),
        ('COMPUTER', 'Computer'),
        ('SOFTWARE', 'Software'),
        ('OTHER', 'Other'),
    ]
    
    DEPRECIATION_METHODS = [
        ('STRAIGHT_LINE', 'Straight Line'),
        ('DECLINING_BALANCE', 'Declining Balance'),
        ('UNITS_OF_PRODUCTION', 'Units of Production'),
    ]
    
    name = models.CharField(max_length=200)
    asset_code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=ASSET_CATEGORIES)
    description = models.TextField(blank=True)
    purchase_date = models.DateField()
    purchase_cost = models.DecimalField(max_digits=15, decimal_places=2)
    salvage_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    useful_life_years = models.PositiveIntegerField()
    depreciation_method = models.CharField(max_length=20, choices=DEPRECIATION_METHODS, default='STRAIGHT_LINE')
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    location = models.CharField(max_length=200, blank=True)
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['asset_code']
    
    def __str__(self):
        return f"{self.asset_code} - {self.name}"
    
    @property
    def book_value(self):
        """Current book value of the asset"""
        return self.purchase_cost - self.accumulated_depreciation
    
    @property
    def annual_depreciation(self):
        """Annual depreciation amount"""
        if self.depreciation_method == 'STRAIGHT_LINE':
            return (self.purchase_cost - self.salvage_value) / self.useful_life_years
        return 0  # Other methods would require more complex calculations
    
    def calculate_depreciation(self, as_of_date=None):
        """Calculate depreciation up to a specific date"""
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        
        if as_of_date is None:
            as_of_date = timezone.now().date()
        
        if as_of_date <= self.purchase_date:
            return 0
        
        years_elapsed = relativedelta(as_of_date, self.purchase_date).years
        months_elapsed = relativedelta(as_of_date, self.purchase_date).months
        
        total_months = years_elapsed * 12 + months_elapsed
        total_useful_months = self.useful_life_years * 12
        
        if total_months >= total_useful_months:
            return self.purchase_cost - self.salvage_value
        
        if self.depreciation_method == 'STRAIGHT_LINE':
            monthly_depreciation = self.annual_depreciation / 12
            return monthly_depreciation * total_months
        
        return 0