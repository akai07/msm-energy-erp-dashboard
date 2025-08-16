from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'material-categories', views.MaterialCategoryViewSet)
router.register(r'materials', views.MaterialViewSet)
router.register(r'warehouses', views.WarehouseViewSet)
router.register(r'stock-movements', views.StockMovementViewSet)
router.register(r'purchase-orders', views.PurchaseOrderViewSet)
router.register(r'material-receipts', views.MaterialReceiptViewSet)
router.register(r'stock-adjustments', views.StockAdjustmentViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    
    # Dashboard and reporting endpoints
    path('dashboard/stats/', views.InventoryDashboardView.as_view({'get': 'stats'}), name='inventory-dashboard-stats'),
    path('dashboard/reports/', views.InventoryDashboardView.as_view({'get': 'reports'}), name='inventory-dashboard-reports'),
    
    # Supplier specific endpoints
    path('suppliers/<int:pk>/purchase-orders/', views.SupplierViewSet.as_view({'get': 'purchase_orders'}), name='supplier-purchase-orders'),
    path('suppliers/<int:pk>/performance/', views.SupplierViewSet.as_view({'get': 'performance'}), name='supplier-performance'),
    path('suppliers/top/', views.SupplierViewSet.as_view({'get': 'top_suppliers'}), name='top-suppliers'),
    
    # Material specific endpoints
    path('materials/low-stock/', views.MaterialViewSet.as_view({'get': 'low_stock'}), name='materials-low-stock'),
    path('materials/out-of-stock/', views.MaterialViewSet.as_view({'get': 'out_of_stock'}), name='materials-out-of-stock'),
    path('materials/reorder-required/', views.MaterialViewSet.as_view({'get': 'reorder_required'}), name='materials-reorder-required'),
    path('materials/<int:pk>/stock-movements/', views.MaterialViewSet.as_view({'get': 'stock_movements'}), name='material-stock-movements'),
    path('materials/<int:pk>/adjust-stock/', views.MaterialViewSet.as_view({'post': 'adjust_stock'}), name='material-adjust-stock'),
    
    # Warehouse specific endpoints
    path('warehouses/<int:pk>/stock-levels/', views.WarehouseViewSet.as_view({'get': 'stock_levels'}), name='warehouse-stock-levels'),
    
    # Purchase Order specific endpoints
    path('purchase-orders/<int:pk>/approve/', views.PurchaseOrderViewSet.as_view({'post': 'approve'}), name='purchase-order-approve'),
    path('purchase-orders/<int:pk>/send/', views.PurchaseOrderViewSet.as_view({'post': 'send'}), name='purchase-order-send'),
    path('purchase-orders/<int:pk>/cancel/', views.PurchaseOrderViewSet.as_view({'post': 'cancel'}), name='purchase-order-cancel'),
    path('purchase-orders/pending/', views.PurchaseOrderViewSet.as_view({'get': 'pending'}), name='purchase-orders-pending'),
    path('purchase-orders/overdue/', views.PurchaseOrderViewSet.as_view({'get': 'overdue'}), name='purchase-orders-overdue'),
    
    # Material Receipt specific endpoints
    path('material-receipts/<int:pk>/confirm/', views.MaterialReceiptViewSet.as_view({'post': 'confirm'}), name='material-receipt-confirm'),
    path('material-receipts/pending/', views.MaterialReceiptViewSet.as_view({'get': 'pending'}), name='material-receipts-pending'),
    
    # Stock Adjustment specific endpoints
    path('stock-adjustments/<int:pk>/approve/', views.StockAdjustmentViewSet.as_view({'post': 'approve'}), name='stock-adjustment-approve'),
    path('stock-adjustments/pending/', views.StockAdjustmentViewSet.as_view({'get': 'pending'}), name='stock-adjustments-pending'),
]