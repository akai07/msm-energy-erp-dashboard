from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel
import uuid


class Customer(BaseModel):
    """Customer model for CRM"""
    CUSTOMER_TYPES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('government', 'Government'),
    ]
    
    customer_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='company')
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_terms = models.IntegerField(default=30, help_text="Payment terms in days")
    sales_representative = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.customer_id} - {self.name}"
    
    def get_outstanding_amount(self):
        """Calculate total outstanding amount for this customer"""
        from .models import Invoice
        outstanding = Invoice.objects.filter(
            customer=self,
            status__in=['pending', 'overdue'],
            is_active=True
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0
        return outstanding
    
    def get_total_sales(self, year=None):
        """Get total sales for this customer"""
        from .models import SalesOrder
        orders = SalesOrder.objects.filter(customer=self, is_active=True)
        if year:
            orders = orders.filter(order_date__year=year)
        return orders.aggregate(total=models.Sum('total_amount'))['total'] or 0


class ProductCategory(BaseModel):
    """Product category model"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Product Categories'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Product(BaseModel):
    """Product model"""
    PRODUCT_TYPES = [
        ('finished_good', 'Finished Good'),
        ('raw_material', 'Raw Material'),
        ('semi_finished', 'Semi-Finished'),
        ('service', 'Service'),
    ]
    
    product_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='finished_good')
    unit_of_measure = models.CharField(max_length=20, default='Piece')
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    dimensions = models.CharField(max_length=100, blank=True, help_text="L x W x H")
    material_grade = models.CharField(max_length=50, blank=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_order_quantity = models.IntegerField(default=1)
    lead_time_days = models.IntegerField(default=7)
    is_customizable = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['product_id']
    
    def __str__(self):
        return f"{self.product_id} - {self.name}"
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.selling_price > 0:
            return ((self.selling_price - self.cost_price) / self.selling_price * 100)
        return 0


class SalesOrder(BaseModel):
    """Sales order model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_production', 'In Production'),
        ('ready_to_ship', 'Ready to Ship'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    sales_representative = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-order_date', '-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"
    
    def calculate_totals(self):
        """Calculate order totals from line items"""
        line_items = self.salesorderlineitem_set.filter(is_active=True)
        self.subtotal = sum(item.line_total for item in line_items)
        
        # Calculate tax (assuming 18% GST)
        self.tax_amount = self.subtotal * Decimal('0.18')
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.save()
    
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['draft', 'confirmed']


class SalesOrderLineItem(BaseModel):
    """Sales order line item model"""
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    specifications = models.TextField(blank=True, help_text="Custom specifications for this item")
    delivery_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calculate line total
        discounted_price = self.unit_price * (1 - self.discount_percentage / 100)
        self.line_total = discounted_price * self.quantity
        super().save(*args, **kwargs)
        
        # Update order totals
        self.sales_order.calculate_totals()


class Quotation(BaseModel):
    """Quotation model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    quotation_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    quotation_date = models.DateField(default=timezone.now)
    valid_until = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    sales_representative = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-quotation_date']
    
    def __str__(self):
        return f"{self.quotation_number} - {self.customer.name}"
    
    def convert_to_order(self):
        """Convert quotation to sales order"""
        if self.status != 'accepted':
            raise ValueError("Only accepted quotations can be converted to orders")
        
        # Create sales order
        order = SalesOrder.objects.create(
            customer=self.customer,
            expected_delivery_date=self.valid_until + timezone.timedelta(days=30),
            sales_representative=self.sales_representative,
            subtotal=self.subtotal,
            tax_amount=self.tax_amount,
            discount_amount=self.discount_amount,
            total_amount=self.total_amount,
            notes=self.notes,
            terms_and_conditions=self.terms_and_conditions,
        )
        
        # Copy line items
        for quote_item in self.quotationlineitem_set.filter(is_active=True):
            SalesOrderLineItem.objects.create(
                sales_order=order,
                product=quote_item.product,
                quantity=quote_item.quantity,
                unit_price=quote_item.unit_price,
                discount_percentage=quote_item.discount_percentage,
                line_total=quote_item.line_total,
                specifications=quote_item.specifications,
            )
        
        return order


class QuotationLineItem(BaseModel):
    """Quotation line item model"""
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    specifications = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # Calculate line total
        discounted_price = self.unit_price * (1 - self.discount_percentage / 100)
        self.line_total = discounted_price * self.quantity
        super().save(*args, **kwargs)


class Invoice(BaseModel):
    """Invoice model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-invoice_date']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"
    
    @property
    def outstanding_amount(self):
        return self.total_amount - self.paid_amount
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status == 'pending'
    
    def mark_as_paid(self, amount=None):
        """Mark invoice as paid"""
        if amount is None:
            amount = self.outstanding_amount
        
        self.paid_amount += amount
        if self.paid_amount >= self.total_amount:
            self.status = 'paid'
        self.save()


class Payment(BaseModel):
    """Payment model"""
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('upi', 'UPI'),
        ('other', 'Other'),
    ]
    
    payment_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=True, blank=True)
    payment_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.payment_number} - {self.customer.name} - {self.amount}"