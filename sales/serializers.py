from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Customer, ProductCategory, Product, SalesOrder, SalesOrderLineItem,
    Quotation, QuotationLineItem, Invoice, Payment
)


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model"""
    
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'customer_type', 'contact_person', 'email', 'phone',
            'website', 'billing_address', 'shipping_address', 'city', 'state',
            'country', 'postal_code', 'credit_limit', 'payment_terms',
            'outstanding_balance', 'tax_number', 'currency', 'notes',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductCategorySerializer(serializers.ModelSerializer):
    """Serializer for Product Category model"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = ProductCategory
        fields = [
            'id', 'name', 'code', 'description', 'parent', 'parent_name',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    profit_margin_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 'product_type',
            'description', 'specifications', 'unit_price', 'cost_price',
            'profit_margin_percentage', 'unit_of_measure', 'minimum_order_quantity',
            'track_inventory', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'profit_margin_percentage']


class SalesOrderLineItemSerializer(serializers.ModelSerializer):
    """Serializer for Sales Order Line Item model"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    line_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = SalesOrderLineItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity',
            'unit_price', 'discount_percentage', 'line_total', 'notes'
        ]
        read_only_fields = ['id', 'line_total']


class SalesOrderSerializer(serializers.ModelSerializer):
    """Serializer for Sales Order model"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    line_items = SalesOrderLineItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'customer', 'customer_name', 'status', 'priority',
            'order_date', 'expected_delivery_date', 'reference', 'subtotal',
            'tax_amount', 'discount_amount', 'shipping_amount', 'total_amount',
            'notes', 'terms_and_conditions', 'line_items', 'created_by',
            'created_by_name', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_amount']


class SalesOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Sales Orders with line items"""
    line_items = SalesOrderLineItemSerializer(many=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'customer', 'status', 'priority', 'order_date', 'expected_delivery_date',
            'reference', 'subtotal', 'tax_amount', 'discount_amount',
            'shipping_amount', 'notes', 'terms_and_conditions', 'line_items'
        ]
    
    def create(self, validated_data):
        line_items_data = validated_data.pop('line_items')
        sales_order = SalesOrder.objects.create(**validated_data)
        
        for line_item_data in line_items_data:
            SalesOrderLineItem.objects.create(sales_order=sales_order, **line_item_data)
        
        sales_order.calculate_total()
        return sales_order


class QuotationLineItemSerializer(serializers.ModelSerializer):
    """Serializer for Quotation Line Item model"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    line_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = QuotationLineItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity',
            'unit_price', 'discount_percentage', 'line_total', 'notes'
        ]
        read_only_fields = ['id', 'line_total']


class QuotationSerializer(serializers.ModelSerializer):
    """Serializer for Quotation model"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    line_items = QuotationLineItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Quotation
        fields = [
            'id', 'quotation_number', 'customer', 'customer_name', 'status',
            'quotation_date', 'valid_until', 'reference', 'subtotal',
            'tax_amount', 'discount_amount', 'total_amount', 'notes',
            'terms_and_conditions', 'line_items', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_amount']


class QuotationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Quotations with line items"""
    line_items = QuotationLineItemSerializer(many=True)
    
    class Meta:
        model = Quotation
        fields = [
            'customer', 'status', 'quotation_date', 'valid_until', 'reference',
            'subtotal', 'tax_amount', 'discount_amount', 'notes',
            'terms_and_conditions', 'line_items'
        ]
    
    def create(self, validated_data):
        line_items_data = validated_data.pop('line_items')
        quotation = Quotation.objects.create(**validated_data)
        
        for line_item_data in line_items_data:
            QuotationLineItem.objects.create(quotation=quotation, **line_item_data)
        
        quotation.calculate_total()
        return quotation


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    sales_order_number = serializers.CharField(source='sales_order.order_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    balance_due = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'customer', 'customer_name', 'sales_order',
            'sales_order_number', 'status', 'invoice_date', 'due_date',
            'subtotal', 'tax_amount', 'discount_amount', 'total_amount',
            'paid_amount', 'balance_due', 'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'balance_due']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'customer', 'customer_name', 'invoice',
            'invoice_number', 'payment_method', 'amount', 'payment_date',
            'status', 'transaction_id', 'reference', 'bank_details', 'notes',
            'created_by', 'created_by_name', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SalesDashboardStatsSerializer(serializers.Serializer):
    """Serializer for Sales Dashboard Statistics"""
    total_customers = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_orders = serializers.IntegerField()
    overdue_invoices = serializers.IntegerField()
    total_outstanding = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Monthly trends
    monthly_revenue = serializers.ListField(child=serializers.DictField())
    monthly_orders = serializers.ListField(child=serializers.DictField())
    
    # Top customers
    top_customers = serializers.ListField(child=serializers.DictField())
    
    # Top products
    top_products = serializers.ListField(child=serializers.DictField())
    
    # Order status distribution
    order_status_distribution = serializers.DictField()
    
    # Payment status distribution
    payment_status_distribution = serializers.DictField()


class SalesReportSerializer(serializers.Serializer):
    """Serializer for Sales Reports"""
    report_type = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Detailed data
    sales_data = serializers.ListField(child=serializers.DictField())
    customer_analysis = serializers.ListField(child=serializers.DictField())
    product_analysis = serializers.ListField(child=serializers.DictField())