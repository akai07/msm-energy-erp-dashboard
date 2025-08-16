from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QualityStandardViewSet, QualityInspectionViewSet, 
    QualityAlertViewSet, QualityMetricsViewSet
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'quality-standards', QualityStandardViewSet)
router.register(r'quality-inspections', QualityInspectionViewSet)
router.register(r'quality-alerts', QualityAlertViewSet)
router.register(r'quality-metrics', QualityMetricsViewSet)

# Quality Inspection specific URLs
quality_inspection_urls = [
    path('pending/', QualityInspectionViewSet.as_view({'get': 'pending_inspections'}), name='quality-inspections-pending'),
    path('summary/', QualityInspectionViewSet.as_view({'get': 'inspection_summary'}), name='quality-inspections-summary'),
]

# Quality Alert specific URLs
quality_alert_urls = [
    path('<int:pk>/resolve/', QualityAlertViewSet.as_view({'post': 'resolve'}), name='quality-alert-resolve'),
    path('active/', QualityAlertViewSet.as_view({'get': 'active_alerts'}), name='quality-alerts-active'),
]

# Quality Metric specific URLs
quality_metric_urls = [
    path('trends/', QualityMetricsViewSet.as_view({'get': 'quality_trends'}), name='quality-metrics-trends'),
]

urlpatterns = [
    # Include the router URLs
    path('api/', include(router.urls)),
    
    # Quality Inspection URLs
    path('api/quality-inspections/', include(quality_inspection_urls)),
    
    # Quality Alert URLs
    path('api/quality-alerts/', include(quality_alert_urls)),
    
    # Quality Metric URLs
    path('api/quality-metrics/', include(quality_metric_urls)),
]

# URL patterns summary:
# 
# Quality Standards:
# - GET /api/quality-standards/ - List all quality standards
# - POST /api/quality-standards/ - Create new quality standard
# - GET /api/quality-standards/{id}/ - Get specific quality standard
# - PUT /api/quality-standards/{id}/ - Update quality standard
# - DELETE /api/quality-standards/{id}/ - Delete quality standard
# 
# Quality Inspections:
# - GET /api/quality-inspections/ - List all quality inspections
# - POST /api/quality-inspections/ - Create new quality inspection
# - GET /api/quality-inspections/{id}/ - Get specific quality inspection
# - PUT /api/quality-inspections/{id}/ - Update quality inspection
# - DELETE /api/quality-inspections/{id}/ - Delete quality inspection
# - GET /api/quality-inspections/pending/ - Get pending inspections
# - GET /api/quality-inspections/summary/ - Get inspection summary
# 
# Quality Alerts:
# - GET /api/quality-alerts/ - List all quality alerts
# - POST /api/quality-alerts/ - Create new quality alert
# - GET /api/quality-alerts/{id}/ - Get specific quality alert
# - PUT /api/quality-alerts/{id}/ - Update quality alert
# - DELETE /api/quality-alerts/{id}/ - Delete quality alert
# - POST /api/quality-alerts/{id}/resolve/ - Resolve quality alert
# - GET /api/quality-alerts/active/ - Get active alerts
# 
# Quality Metrics:
# - GET /api/quality-metrics/ - List all quality metrics
# - POST /api/quality-metrics/ - Create new quality metric
# - GET /api/quality-metrics/{id}/ - Get specific quality metric
# - PUT /api/quality-metrics/{id}/ - Update quality metric
# - DELETE /api/quality-metrics/{id}/ - Delete quality metric
# - GET /api/quality-metrics/trends/ - Get quality trends