from django.contrib import admin
from .models import (
    Customer, ProductCategory, Product, SalesOrder, SalesOrderLineItem,
    Quotation, QuotationLineItem, Invoice, Payment
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'customer_id', 'name', 'customer_type', 'email', 'phone',
        'credit_limit', 'created_at'
    ]
    list_filter = ['customer_type', 'created_at', 'is_active']
    search_fields = ['name', 'email', 'phone', 'contact_person']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'customer_id', 'name', 'customer_type', 'contact_person',
                'email', 'phone'
            )
        }),
        ('Address', {
            'fields': (
                'address', 'city', 'state', 'country', 'postal_code'
            )
        }),
        ('Financial Information', {
            'fields': (
                'credit_limit', 'payment_terms', 'gst_number', 'pan_number'
            )
        }),
        ('Sales', {
            'fields': ('sales_representative',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        })
    )


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent_category', 'created_at']
    list_filter = ['created_at', 'is_active']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'product_id', 'name', 'category', 'product_type',
        'selling_price', 'cost_price'
    ]
    list_filter = ['category', 'product_type', 'unit_of_measure', 'created_at']
    search_fields = ['name', 'product_id', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'product_id', 'name', 'category', 'product_type',
                'description', 'unit_of_measure'
            )
        }),
        ('Pricing', {
            'fields': (
                'selling_price', 'cost_price', 'minimum_order_quantity'
            )
        }),
        ('Physical Properties', {
            'fields': ('weight', 'dimensions', 'material_grade')
        }),
        ('Production', {
            'fields': ('lead_time_days', 'is_customizable')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        })
    )


class SalesOrderLineItemInline(admin.TabularInline):
    model = SalesOrderLineItem
    extra = 1
    readonly_fields = ['line_total']


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer', 'status', 'priority',
        'order_date', 'total_amount', 'created_by'
    ]
    list_filter = ['status', 'priority', 'order_date', 'created_at']
    search_fields = ['order_number', 'customer__name', 'reference']
    readonly_fields = ['created_at', 'updated_at', 'total_amount']
    inlines = [SalesOrderLineItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_number', 'customer', 'status', 'priority',
                'order_date', 'expected_delivery_date', 'reference'
            )
        }),
        ('Financial', {
            'fields': (
                'subtotal', 'tax_amount', 'discount_amount',
                'shipping_amount', 'total_amount'
            )
        }),
        ('Additional Info', {
            'fields': ('notes', 'terms_and_conditions')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        })
    )


class QuotationLineItemInline(admin.TabularInline):
    model = QuotationLineItem
    extra = 1
    readonly_fields = ['line_total']


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = [
        'quotation_number', 'customer', 'status',
        'quotation_date', 'valid_until', 'total_amount'
    ]
    list_filter = ['status', 'quotation_date', 'valid_until', 'created_at']
    search_fields = ['quotation_number', 'customer__name', 'reference']
    readonly_fields = ['created_at', 'updated_at', 'total_amount']
    inlines = [QuotationLineItemInline]
    
    fieldsets = (
        ('Quotation Information', {
            'fields': (
                'quotation_number', 'customer', 'status',
                'quotation_date', 'valid_until', 'reference'
            )
        }),
        ('Financial', {
            'fields': (
                'subtotal', 'tax_amount', 'discount_amount',
                'total_amount'
            )
        }),
        ('Additional Info', {
            'fields': ('notes', 'terms_and_conditions')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        })
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'customer', 'status',
        'invoice_date', 'due_date', 'total_amount', 'paid_amount'
    ]
    list_filter = ['status', 'invoice_date', 'due_date', 'created_at']
    search_fields = ['invoice_number', 'customer__name', 'sales_order__order_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Invoice Information', {
            'fields': (
                'invoice_number', 'customer', 'sales_order', 'status',
                'invoice_date', 'due_date'
            )
        }),
        ('Financial', {
            'fields': (
                'subtotal', 'tax_amount', 'discount_amount',
                'total_amount', 'paid_amount'
            )
        }),
        ('Additional Info', {
            'fields': ('notes',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'created_by', 'is_active'),
            'classes': ('collapse',)
        })
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_number', 'customer', 'payment_method',
        'amount', 'payment_date'
    ]
    list_filter = ['payment_method', 'payment_date', 'created_at']
    search_fields = ['payment_number', 'customer__name', 'reference_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'payment_number', 'customer', 'invoice', 'payment_method',
                'amount', 'payment_date'
            )
        }),
        ('Transaction Details', {
            'fields': (
                'reference_number',
            )
        }),
        ('Additional Info', {
            'fields': ('notes',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'created_by', 'is_active'),
            'classes': ('collapse',)
        })
    )