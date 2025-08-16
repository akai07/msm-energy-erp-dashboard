from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'readings', views.EnergyReadingViewSet)
router.register(r'alerts', views.EnergyAlertViewSet)
router.register(r'efficiency-metrics', views.EnergyEfficiencyMetricViewSet)
router.register(r'targets', views.EnergyTargetViewSet)
router.register(r'reports', views.EnergyReportViewSet)

app_name = 'energy_dashboard'

urlpatterns = [
    # Include router URLs
    path('api/', include(router.urls)),
    
    # Dashboard statistics
    path('api/dashboard/stats/', views.EnergyDashboardStatsView.as_view(), name='dashboard-stats'),
    
    # Energy consumption trends
    path('api/consumption/trends/', views.EnergyConsumptionTrendView.as_view(), name='consumption-trends'),
    
    # CSV upload
    path('api/upload/csv/', views.CSVUploadView.as_view(), name='csv-upload'),
    
    # Energy optimization recommendations
    path('api/optimization/recommendations/', views.EnergyOptimizationView.as_view(), name='optimization-recommendations'),
    
    # Additional energy reading endpoints
    path('api/readings/latest/', views.EnergyReadingViewSet.as_view({'get': 'latest'}), name='readings-latest'),
    path('api/readings/summary/', views.EnergyReadingViewSet.as_view({'get': 'summary'}), name='readings-summary'),
    
    # Alert management endpoints
    path('api/alerts/active/', views.EnergyAlertViewSet.as_view({'get': 'active'}), name='alerts-active'),
    path('api/alerts/<int:pk>/acknowledge/', views.EnergyAlertViewSet.as_view({'post': 'acknowledge'}), name='alert-acknowledge'),
    
    # Efficiency metrics endpoints
    path('api/efficiency-metrics/trend/', views.EnergyEfficiencyMetricViewSet.as_view({'get': 'trend'}), name='efficiency-trend'),
    
    # Target progress endpoints
    path('api/targets/progress/', views.EnergyTargetViewSet.as_view({'get': 'progress'}), name='targets-progress'),
    
    # Steel Industry data processing endpoints
    path('api/steel-industry/process/', views.SteelIndustryDataAPIView.as_view(), name='steel-industry-process'),
    path('api/steel-industry/correlations/', views.SteelIndustryDataAPIView.as_view(), name='steel-industry-correlations'),
    
    # Energy correlation analysis
    path('api/correlations/', views.EnergyCorrelationAPIView.as_view(), name='energy-correlations'),
]