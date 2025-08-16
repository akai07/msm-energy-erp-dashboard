from django.contrib import admin
from .models import (
    Supplier, MaterialCategory, Material, Warehouse, StockMovement,
    PurchaseOrder, PurchaseOrderLineItem, MaterialReceipt, MaterialReceiptLineItem,
    StockAdjustment, StockAdjustmentLineItem
)


class PurchaseOrderLineItemInline(admin.TabularInline):
    """Inline admin for Purchase Order Line Items"""
    model = PurchaseOrderLineItem
    extra = 1
    fields = ['material', 'quantity_ordered', 'unit_price', 'discount_percentage', 'line_total', 'specifications']
    readonly_fields = ['line_total']


class MaterialReceiptLineItemInline(admin.TabularInline):
    """Inline admin for Material Receipt Line Items"""
    model = MaterialReceiptLineItem
    extra = 1
    fields = ['material', 'quantity_received', 'unit_cost', 'quality_status', 'batch_number', 'notes']
    readonly_fields = []


class StockAdjustmentLineItemInline(admin.TabularInline):
    """Inline admin for Stock Adjustment Line Items"""
    model = StockAdjustmentLineItem
    extra = 1
    fields = ['material', 'current_stock', 'adjusted_stock', 'difference', 'unit_cost', 'notes']
    readonly_fields = ['difference', 'total_value']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin interface for Supplier model"""
    list_display = [
        'supplier_id', 'name', 'supplier_type', 'contact_person', 'email', 'phone',
        'city', 'country', 'credit_rating', 'is_active', 'created_at'
    ]
    list_filter = ['supplier_type', 'country', 'credit_rating', 'is_active', 'created_at']
    search_fields = ['supplier_id', 'name', 'contact_person', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('supplier_id', 'name', 'supplier_type', 'contact_person', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Business Details', {
            'fields': ('gst_number', 'pan_number', 'payment_terms', 'credit_rating', 'is_approved')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    """Admin interface for Material Category model"""
    list_display = ['name', 'code', 'parent_category', 'is_active', 'created_at']
    list_filter = ['parent_category', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'parent_category', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    """Admin interface for Material model"""
    list_display = [
        'material_id', 'name', 'category', 'material_type', 'unit_of_measure',
        'current_stock', 'reorder_point', 'standard_cost', 'is_active'
    ]
    list_filter = ['category', 'material_type', 'unit_of_measure', 'is_active', 'created_at']
    search_fields = ['material_id', 'name', 'description']
    readonly_fields = ['current_stock', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('material_id', 'name', 'category', 'material_type', 'description')
        }),
        ('Specifications', {
            'fields': ('specifications', 'unit_of_measure', 'standard_cost', 'grade')
        }),
        ('Stock Management', {
            'fields': ('current_stock', 'minimum_stock_level', 'reorder_point', 'maximum_stock_level', 'reorder_quantity', 'lead_time_days')
        }),
        ('Additional Information', {
            'fields': ('storage_location', 'supplier', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    """Admin interface for Warehouse model"""
    list_display = [
        'name', 'code', 'city', 'state', 'manager',
        'capacity', 'is_main_warehouse', 'is_active', 'created_at'
    ]
    list_filter = ['is_main_warehouse', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'is_main_warehouse')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state')
        }),
        ('Management', {
            'fields': ('capacity', 'manager')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Admin interface for Stock Movement model"""
    list_display = [
        'material', 'warehouse', 'transaction_type', 'quantity', 'unit_cost',
        'reference', 'created_at'
    ]
    list_filter = ['transaction_type', 'warehouse', 'created_at']
    search_fields = ['material__name', 'material__material_id', 'reference', 'notes']
    readonly_fields = ['previous_stock', 'current_stock', 'total_cost', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Movement Details', {
            'fields': ('material', 'warehouse', 'transaction_type', 'quantity', 'unit_cost', 'total_cost')
        }),
        ('Stock Information', {
            'fields': ('previous_stock', 'current_stock')
        }),
        ('Reference', {
            'fields': ('reference', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Admin interface for Purchase Order model"""
    list_display = [
        'po_number', 'supplier', 'status', 'order_date', 'expected_delivery_date',
        'total_amount', 'buyer', 'created_at'
    ]
    list_filter = ['status', 'supplier', 'priority', 'order_date', 'expected_delivery_date', 'created_at']
    search_fields = ['po_number', 'supplier__name', 'notes']
    readonly_fields = ['subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at']
    inlines = [PurchaseOrderLineItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('po_number', 'supplier', 'status', 'priority')
        }),
        ('Dates', {
            'fields': ('order_date', 'expected_delivery_date')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms_and_conditions', 'buyer')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(MaterialReceipt)
class MaterialReceiptAdmin(admin.ModelAdmin):
    """Admin interface for Material Receipt model"""
    list_display = [
        'receipt_number', 'purchase_order', 'supplier', 'receipt_date',
        'received_by', 'warehouse', 'created_at'
    ]
    list_filter = ['supplier', 'warehouse', 'receipt_date', 'created_at']
    search_fields = ['receipt_number', 'purchase_order__po_number', 'supplier__name', 'invoice_number']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MaterialReceiptLineItemInline]
    
    fieldsets = (
        ('Receipt Information', {
            'fields': ('receipt_number', 'purchase_order', 'supplier', 'warehouse')
        }),
        ('Receipt Details', {
            'fields': ('receipt_date', 'received_by', 'invoice_number')
        }),
        ('Transport Information', {
            'fields': ('vehicle_number', 'driver_name')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    """Admin interface for Stock Adjustment model"""
    list_display = [
        'adjustment_number', 'adjustment_type', 'adjustment_date',
        'approved_by', 'created_by', 'is_active', 'created_at'
    ]
    list_filter = ['adjustment_type', 'adjustment_date', 'is_active', 'created_at']
    search_fields = ['adjustment_number', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [StockAdjustmentLineItemInline]
    
    fieldsets = (
        ('Adjustment Information', {
            'fields': ('adjustment_number', 'adjustment_type', 'adjustment_date')
        }),
        ('Details', {
            'fields': ('reason', 'approved_by', 'created_by')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


# Register the line item models separately for direct access if needed
@admin.register(PurchaseOrderLineItem)
class PurchaseOrderLineItemAdmin(admin.ModelAdmin):
    """Admin interface for Purchase Order Line Item model"""
    list_display = ['purchase_order', 'material', 'quantity_ordered', 'quantity_received', 'unit_price', 'line_total']
    list_filter = ['purchase_order__status', 'material__category']
    search_fields = ['purchase_order__po_number', 'material__name', 'material__material_id']
    readonly_fields = ['line_total', 'quantity_pending', 'is_fully_received']


@admin.register(MaterialReceiptLineItem)
class MaterialReceiptLineItemAdmin(admin.ModelAdmin):
    """Admin interface for Material Receipt Line Item model"""
    list_display = ['material_receipt', 'material', 'quantity_received', 'unit_cost', 'quality_status']
    list_filter = ['material__category', 'quality_status']
    search_fields = ['material_receipt__receipt_number', 'material__name', 'material__material_id']
    readonly_fields = []


@admin.register(StockAdjustmentLineItem)
class StockAdjustmentLineItemAdmin(admin.ModelAdmin):
    """Admin interface for Stock Adjustment Line Item model"""
    list_display = ['stock_adjustment', 'material', 'current_stock', 'adjusted_stock', 'difference', 'total_value']
    list_filter = ['stock_adjustment__adjustment_type', 'stock_adjustment__adjustment_date']
    search_fields = ['stock_adjustment__adjustment_number', 'material__name', 'material__material_id']
    readonly_fields = ['difference', 'total_value']