from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Supplier, MaterialCategory, Material, Warehouse, StockMovement,
    PurchaseOrder, PurchaseOrderLineItem, MaterialReceipt, MaterialReceiptLineItem,
    StockAdjustment, StockAdjustmentLineItem
)


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for Supplier model"""
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'supplier_type', 'contact_person', 'email', 'phone',
            'website', 'address', 'city', 'state', 'country', 'postal_code',
            'tax_number', 'payment_terms', 'credit_limit', 'currency', 'rating',
            'notes', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MaterialCategorySerializer(serializers.ModelSerializer):
    """Serializer for Material Category model"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = MaterialCategory
        fields = [
            'id', 'name', 'code', 'description', 'parent', 'parent_name',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MaterialSerializer(serializers.ModelSerializer):
    """Serializer for Material model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_status = serializers.SerializerMethodField()
    stock_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Material
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 'material_type',
            'description', 'specifications', 'unit_of_measure', 'unit_cost',
            'current_stock', 'minimum_stock_level', 'reorder_level', 'maximum_stock_level',
            'stock_status', 'stock_value', 'notes', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'current_stock', 'stock_status', 'stock_value', 'created_at', 'updated_at']
    
    def get_stock_status(self, obj):
        """Get stock status based on current stock levels"""
        return obj.get_stock_status()
    
    def get_stock_value(self, obj):
        """Get total stock value"""
        return obj.get_stock_value()


class WarehouseSerializer(serializers.ModelSerializer):
    """Serializer for Warehouse model"""
    
    class Meta:
        model = Warehouse
        fields = [
            'id', 'name', 'code', 'warehouse_type', 'description', 'address',
            'city', 'state', 'country', 'postal_code', 'capacity',
            'manager_name', 'manager_phone', 'manager_email',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for Stock Movement model"""
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_sku = serializers.CharField(source='material.sku', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'material', 'material_name', 'material_sku', 'warehouse',
            'warehouse_name', 'movement_type', 'quantity', 'unit_cost',
            'reference_type', 'reference_id', 'reference_number',
            'movement_date', 'notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PurchaseOrderLineItemSerializer(serializers.ModelSerializer):
    """Serializer for Purchase Order Line Item model"""
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_sku = serializers.CharField(source='material.sku', read_only=True)
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = PurchaseOrderLineItem
        fields = [
            'id', 'material', 'material_name', 'material_sku', 'quantity',
            'unit_price', 'total_price', 'notes'
        ]
        read_only_fields = ['id', 'total_price']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for Purchase Order model"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    line_items = PurchaseOrderLineItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier', 'supplier_name', 'status', 'priority',
            'order_date', 'expected_delivery_date', 'reference', 'subtotal',
            'tax_amount', 'discount_amount', 'shipping_amount', 'total_amount',
            'notes', 'terms_and_conditions', 'line_items', 'created_by',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'order_number', 'total_amount', 'created_at', 'updated_at']


class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Purchase Orders with line items"""
    line_items = PurchaseOrderLineItemSerializer(many=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'supplier', 'status', 'priority', 'order_date', 'expected_delivery_date',
            'reference', 'subtotal', 'tax_amount', 'discount_amount',
            'shipping_amount', 'notes', 'terms_and_conditions', 'line_items'
        ]
    
    def create(self, validated_data):
        line_items_data = validated_data.pop('line_items')
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        
        for line_item_data in line_items_data:
            PurchaseOrderLineItem.objects.create(purchase_order=purchase_order, **line_item_data)
        
        purchase_order.calculate_total()
        return purchase_order


class MaterialReceiptLineItemSerializer(serializers.ModelSerializer):
    """Serializer for Material Receipt Line Item model"""
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_sku = serializers.CharField(source='material.sku', read_only=True)
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = MaterialReceiptLineItem
        fields = [
            'id', 'material', 'material_name', 'material_sku', 'quantity_ordered',
            'quantity_received', 'unit_price', 'total_price', 'notes'
        ]
        read_only_fields = ['id', 'total_price']


class MaterialReceiptSerializer(serializers.ModelSerializer):
    """Serializer for Material Receipt model"""
    purchase_order_number = serializers.CharField(source='purchase_order.order_number', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    line_items = MaterialReceiptLineItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = MaterialReceipt
        fields = [
            'id', 'receipt_number', 'purchase_order', 'purchase_order_number',
            'supplier', 'supplier_name', 'warehouse', 'warehouse_name', 'status',
            'receipt_date', 'inspection_date', 'quality_status', 'subtotal',
            'tax_amount', 'discount_amount', 'total_amount', 'notes',
            'line_items', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'receipt_number', 'total_amount', 'created_at', 'updated_at']


class MaterialReceiptCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Material Receipts with line items"""
    line_items = MaterialReceiptLineItemSerializer(many=True)
    
    class Meta:
        model = MaterialReceipt
        fields = [
            'purchase_order', 'supplier', 'warehouse', 'status', 'receipt_date',
            'inspection_date', 'quality_status', 'subtotal', 'tax_amount',
            'discount_amount', 'notes', 'line_items'
        ]
    
    def create(self, validated_data):
        line_items_data = validated_data.pop('line_items')
        material_receipt = MaterialReceipt.objects.create(**validated_data)
        
        for line_item_data in line_items_data:
            MaterialReceiptLineItem.objects.create(material_receipt=material_receipt, **line_item_data)
        
        material_receipt.calculate_total()
        return material_receipt


class StockAdjustmentLineItemSerializer(serializers.ModelSerializer):
    """Serializer for Stock Adjustment Line Item model"""
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_sku = serializers.CharField(source='material.sku', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    
    class Meta:
        model = StockAdjustmentLineItem
        fields = [
            'id', 'material', 'material_name', 'material_sku', 'warehouse',
            'warehouse_name', 'adjustment_quantity', 'reason', 'notes'
        ]
        read_only_fields = ['id']


class StockAdjustmentSerializer(serializers.ModelSerializer):
    """Serializer for Stock Adjustment model"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    line_items = StockAdjustmentLineItemSerializer(many=True, read_only=True)
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = StockAdjustment
        fields = [
            'id', 'adjustment_number', 'adjustment_type', 'adjustment_date',
            'reason', 'reference', 'status', 'total_value', 'notes',
            'line_items', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'adjustment_number', 'total_value', 'created_at', 'updated_at']


class StockAdjustmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Stock Adjustments with line items"""
    line_items = StockAdjustmentLineItemSerializer(many=True)
    
    class Meta:
        model = StockAdjustment
        fields = [
            'adjustment_type', 'adjustment_date', 'reason', 'reference',
            'status', 'notes', 'line_items'
        ]
    
    def create(self, validated_data):
        line_items_data = validated_data.pop('line_items')
        stock_adjustment = StockAdjustment.objects.create(**validated_data)
        
        for line_item_data in line_items_data:
            StockAdjustmentLineItem.objects.create(stock_adjustment=stock_adjustment, **line_item_data)
        
        stock_adjustment.calculate_total_value()
        return stock_adjustment


class InventoryDashboardStatsSerializer(serializers.Serializer):
    """Serializer for Inventory Dashboard Statistics"""
    total_materials = serializers.IntegerField()
    total_suppliers = serializers.IntegerField()
    total_warehouses = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Stock status counts
    in_stock_count = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    reorder_required_count = serializers.IntegerField()
    
    # Purchase order stats
    pending_purchase_orders = serializers.IntegerField()
    pending_receipts = serializers.IntegerField()
    
    # Recent movements
    recent_movements = serializers.ListField(child=serializers.DictField())
    
    # Top materials by value
    top_materials_by_value = serializers.ListField(child=serializers.DictField())
    
    # Low stock materials
    low_stock_materials = serializers.ListField(child=serializers.DictField())
    
    # Monthly stock movements
    monthly_movements = serializers.ListField(child=serializers.DictField())
    
    # Supplier performance
    supplier_performance = serializers.ListField(child=serializers.DictField())


class InventoryReportSerializer(serializers.Serializer):
    """Serializer for Inventory Reports"""
    report_type = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    # Summary data
    total_materials = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_movements = serializers.IntegerField()
    
    # Detailed data
    materials_data = serializers.ListField(child=serializers.DictField())
    movements_data = serializers.ListField(child=serializers.DictField())
    warehouse_data = serializers.ListField(child=serializers.DictField())
    supplier_data = serializers.ListField(child=serializers.DictField())


class StockLevelSerializer(serializers.Serializer):
    """Serializer for Stock Level information"""
    material_id = serializers.IntegerField()
    material_name = serializers.CharField()
    material_sku = serializers.CharField()
    warehouse_id = serializers.IntegerField()
    warehouse_name = serializers.CharField()
    current_stock = serializers.DecimalField(max_digits=15, decimal_places=3)
    minimum_stock_level = serializers.DecimalField(max_digits=15, decimal_places=3)
    reorder_level = serializers.DecimalField(max_digits=15, decimal_places=3)
    maximum_stock_level = serializers.DecimalField(max_digits=15, decimal_places=3)
    stock_status = serializers.CharField()
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)