from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel


class Supplier(BaseModel):
    """Supplier model for managing vendors"""
    SUPPLIER_TYPES = [
        ('raw_material', 'Raw Material Supplier'),
        ('equipment', 'Equipment Supplier'),
        ('service', 'Service Provider'),
        ('logistics', 'Logistics Provider'),
    ]
    
    supplier_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    supplier_type = models.CharField(max_length=20, choices=SUPPLIER_TYPES, default='raw_material')
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    payment_terms = models.IntegerField(default=30, help_text="Payment terms in days")
    credit_rating = models.CharField(max_length=10, blank=True, help_text="A+, A, B+, B, C")
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.supplier_id} - {self.name}"
    
    def get_total_purchases(self, year=None):
        """Get total purchase amount from this supplier"""
        from .models import PurchaseOrder
        orders = PurchaseOrder.objects.filter(supplier=self, is_active=True)
        if year:
            orders = orders.filter(order_date__year=year)
        return orders.aggregate(total=models.Sum('total_amount'))['total'] or 0


class MaterialCategory(BaseModel):
    """Material category model"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Material Categories'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Material(BaseModel):
    """Material/Inventory item model"""
    MATERIAL_TYPES = [
        ('raw_material', 'Raw Material'),
        ('semi_finished', 'Semi-Finished Good'),
        ('finished_good', 'Finished Good'),
        ('consumable', 'Consumable'),
        ('spare_part', 'Spare Part'),
        ('tool', 'Tool/Equipment'),
    ]
    
    material_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(MaterialCategory, on_delete=models.SET_NULL, null=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES, default='raw_material')
    unit_of_measure = models.CharField(max_length=20, default='Kg')
    standard_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_stock = models.FloatField(default=0)
    minimum_stock_level = models.FloatField(default=0)
    maximum_stock_level = models.FloatField(default=0)
    reorder_point = models.FloatField(default=0)
    reorder_quantity = models.FloatField(default=0)
    lead_time_days = models.IntegerField(default=7)
    storage_location = models.CharField(max_length=100, blank=True)
    specifications = models.TextField(blank=True)
    grade = models.CharField(max_length=50, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['material_id']
    
    def __str__(self):
        return f"{self.material_id} - {self.name}"
    
    @property
    def stock_status(self):
        """Get current stock status"""
        if self.current_stock <= 0:
            return 'out_of_stock'
        elif self.current_stock <= self.minimum_stock_level:
            return 'low_stock'
        elif self.current_stock >= self.maximum_stock_level:
            return 'overstock'
        else:
            return 'normal'
    
    @property
    def needs_reorder(self):
        """Check if material needs to be reordered"""
        return self.current_stock <= self.reorder_point
    
    def update_stock(self, quantity, transaction_type, reference=None):
        """Update stock and create stock movement record"""
        old_stock = self.current_stock
        
        if transaction_type in ['receipt', 'production_receipt', 'adjustment_in']:
            self.current_stock += quantity
        elif transaction_type in ['issue', 'production_issue', 'adjustment_out', 'sale']:
            self.current_stock -= quantity
        
        self.save()
        
        # Create stock movement record
        StockMovement.objects.create(
            material=self,
            transaction_type=transaction_type,
            quantity=quantity,
            previous_stock=old_stock,
            current_stock=self.current_stock,
            reference=reference
        )


class Warehouse(BaseModel):
    """Warehouse/Storage location model"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    capacity = models.FloatField(help_text="Storage capacity in cubic meters")
    is_main_warehouse = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class StockMovement(BaseModel):
    """Stock movement/transaction model"""
    TRANSACTION_TYPES = [
        ('receipt', 'Material Receipt'),
        ('issue', 'Material Issue'),
        ('production_receipt', 'Production Receipt'),
        ('production_issue', 'Production Issue'),
        ('adjustment_in', 'Stock Adjustment In'),
        ('adjustment_out', 'Stock Adjustment Out'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('sale', 'Sale'),
        ('return', 'Return'),
    ]
    
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.FloatField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    previous_stock = models.FloatField()
    current_stock = models.FloatField()
    reference = models.CharField(max_length=100, blank=True, help_text="Reference document number")
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.material.name} - {self.transaction_type} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)


class PurchaseOrder(BaseModel):
    """Purchase order model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('confirmed', 'Confirmed'),
        ('partially_received', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    po_number = models.CharField(max_length=20, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-order_date', '-created_at']
    
    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"
    
    def calculate_totals(self):
        """Calculate order totals from line items"""
        line_items = self.purchaseorderlineitem_set.filter(is_active=True)
        self.subtotal = sum(item.line_total for item in line_items)
        
        # Calculate tax (assuming 18% GST)
        self.tax_amount = self.subtotal * Decimal('0.18')
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.save()


class PurchaseOrderLineItem(BaseModel):
    """Purchase order line item model"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity_ordered = models.FloatField()
    quantity_received = models.FloatField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    expected_delivery_date = models.DateField(null=True, blank=True)
    specifications = models.TextField(blank=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.material.name} x {self.quantity_ordered}"
    
    @property
    def quantity_pending(self):
        return self.quantity_ordered - self.quantity_received
    
    @property
    def is_fully_received(self):
        return self.quantity_received >= self.quantity_ordered
    
    def save(self, *args, **kwargs):
        # Calculate line total
        discounted_price = self.unit_price * (1 - self.discount_percentage / 100)
        self.line_total = discounted_price * self.quantity_ordered
        super().save(*args, **kwargs)
        
        # Update order totals
        self.purchase_order.calculate_totals()


class MaterialReceipt(BaseModel):
    """Material receipt model for tracking incoming materials"""
    receipt_number = models.CharField(max_length=20, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    receipt_date = models.DateField(default=timezone.now)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    vehicle_number = models.CharField(max_length=20, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-receipt_date']
    
    def __str__(self):
        return f"{self.receipt_number} - {self.supplier.name}"


class MaterialReceiptLineItem(BaseModel):
    """Material receipt line item model"""
    material_receipt = models.ForeignKey(MaterialReceipt, on_delete=models.CASCADE)
    po_line_item = models.ForeignKey(PurchaseOrderLineItem, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity_received = models.FloatField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    quality_status = models.CharField(max_length=20, choices=[
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('pending_inspection', 'Pending Inspection'),
    ], default='pending_inspection')
    batch_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update PO line item received quantity
        self.po_line_item.quantity_received += self.quantity_received
        self.po_line_item.save()
        
        # Update material stock if quality is accepted
        if self.quality_status == 'accepted':
            self.material.update_stock(
                quantity=self.quantity_received,
                transaction_type='receipt',
                reference=self.material_receipt.receipt_number
            )


class StockAdjustment(BaseModel):
    """Stock adjustment model for inventory corrections"""
    ADJUSTMENT_TYPES = [
        ('physical_count', 'Physical Count Adjustment'),
        ('damage', 'Damage/Loss'),
        ('expiry', 'Expiry'),
        ('theft', 'Theft/Shortage'),
        ('system_error', 'System Error Correction'),
        ('other', 'Other'),
    ]
    
    adjustment_number = models.CharField(max_length=20, unique=True)
    adjustment_date = models.DateField(default=timezone.now)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    reason = models.TextField()
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_adjustments')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_adjustments')
    
    class Meta:
        ordering = ['-adjustment_date']
    
    def __str__(self):
        return f"{self.adjustment_number} - {self.adjustment_type}"


class StockAdjustmentLineItem(BaseModel):
    """Stock adjustment line item model"""
    stock_adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    current_stock = models.FloatField()
    adjusted_stock = models.FloatField()
    difference = models.FloatField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        self.difference = self.adjusted_stock - self.current_stock
        self.total_value = abs(self.difference) * self.unit_cost
        super().save(*args, **kwargs)
        
        # Update material stock
        transaction_type = 'adjustment_in' if self.difference > 0 else 'adjustment_out'
        self.material.update_stock(
            quantity=abs(self.difference),
            transaction_type=transaction_type,
            reference=self.stock_adjustment.adjustment_number
        )