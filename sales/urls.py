from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet)
router.register(r'product-categories', views.ProductCategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'sales-orders', views.SalesOrderViewSet)
router.register(r'quotations', views.QuotationViewSet)
router.register(r'invoices', views.InvoiceViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'dashboard', views.SalesDashboardView, basename='sales-dashboard')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('api/', include(router.urls)),
    
    # Additional custom endpoints
    path('api/customers/<int:pk>/orders/', views.CustomerViewSet.as_view({'get': 'orders'}), name='customer-orders'),
    path('api/customers/<int:pk>/invoices/', views.CustomerViewSet.as_view({'get': 'invoices'}), name='customer-invoices'),
    path('api/customers/<int:pk>/payments/', views.CustomerViewSet.as_view({'get': 'payments'}), name='customer-payments'),
    path('api/customers/top/', views.CustomerViewSet.as_view({'get': 'top_customers'}), name='top-customers'),
    
    path('api/products/top-selling/', views.ProductViewSet.as_view({'get': 'top_selling'}), name='top-selling-products'),
    path('api/products/low-stock/', views.ProductViewSet.as_view({'get': 'low_stock'}), name='low-stock-products'),
    
    path('api/sales-orders/<int:pk>/confirm/', views.SalesOrderViewSet.as_view({'post': 'confirm'}), name='confirm-sales-order'),
    path('api/sales-orders/<int:pk>/cancel/', views.SalesOrderViewSet.as_view({'post': 'cancel'}), name='cancel-sales-order'),
    path('api/sales-orders/<int:pk>/create-invoice/', views.SalesOrderViewSet.as_view({'post': 'create_invoice'}), name='create-invoice-from-order'),
    path('api/sales-orders/pending/', views.SalesOrderViewSet.as_view({'get': 'pending'}), name='pending-sales-orders'),
    path('api/sales-orders/overdue/', views.SalesOrderViewSet.as_view({'get': 'overdue'}), name='overdue-sales-orders'),
    
    path('api/quotations/<int:pk>/accept/', views.QuotationViewSet.as_view({'post': 'accept'}), name='accept-quotation'),
    path('api/quotations/<int:pk>/reject/', views.QuotationViewSet.as_view({'post': 'reject'}), name='reject-quotation'),
    path('api/quotations/<int:pk>/convert-to-order/', views.QuotationViewSet.as_view({'post': 'convert_to_order'}), name='convert-quotation-to-order'),
    path('api/quotations/expired/', views.QuotationViewSet.as_view({'get': 'expired'}), name='expired-quotations'),
    
    path('api/invoices/<int:pk>/mark-paid/', views.InvoiceViewSet.as_view({'post': 'mark_paid'}), name='mark-invoice-paid'),
    path('api/invoices/overdue/', views.InvoiceViewSet.as_view({'get': 'overdue'}), name='overdue-invoices'),
    path('api/invoices/unpaid/', views.InvoiceViewSet.as_view({'get': 'unpaid'}), name='unpaid-invoices'),
    
    path('api/payments/<int:pk>/confirm/', views.PaymentViewSet.as_view({'post': 'confirm'}), name='confirm-payment'),
    
    path('api/dashboard/stats/', views.SalesDashboardView.as_view({'get': 'stats'}), name='sales-dashboard-stats'),
    path('api/dashboard/reports/', views.SalesDashboardView.as_view({'get': 'reports'}), name='sales-reports'),
]

app_name = 'sales'