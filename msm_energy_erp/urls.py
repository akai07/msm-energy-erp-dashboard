from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/core/dashboard/', permanent=False), name='home'),
    
    # Authentication
    path('', include('django.contrib.auth.urls')),
    
    # API endpoints
    path('api/auth/', include('rest_framework.urls')),
    path('api/energy/', include('energy_dashboard.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/production/', include('production.urls')),
    path('api/qa/', include('quality_assurance.urls')),
    path('api/hr/', include('hr.urls')),
    path('api/finance/', include('finance.urls')),
    path('api/core/', include('core.urls')),
    
    # App routes
    path('core/', include('core.urls')),
    path('energy/', include('energy_dashboard.urls')),
    path('sales/', include('sales.urls')),
    path('inventory/', include('inventory.urls')),
    path('production/', include('production.urls')),
    path('qa/', include('quality_assurance.urls')),
    path('hr/', include('hr.urls')),
    path('finance/', include('finance.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "MSM Energy ERP Administration"
admin.site.site_title = "MSM Energy ERP Admin"
admin.site.index_title = "Welcome to MSM Energy ERP Administration"