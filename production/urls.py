from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'production-lines', views.ProductionLineViewSet)
router.register(r'equipment', views.EquipmentViewSet)
router.register(r'production-plans', views.ProductionPlanViewSet)
router.register(r'work-orders', views.WorkOrderViewSet)
router.register(r'bill-of-materials', views.BillOfMaterialsViewSet)
router.register(r'production-entries', views.ProductionEntryViewSet)
router.register(r'quality-checks', views.QualityCheckViewSet)
router.register(r'maintenance-schedules', views.MaintenanceScheduleViewSet)
router.register(r'production-reports', views.ProductionReportViewSet)

# Production Dashboard URLs
production_dashboard_urls = [
    path('stats/', views.ProductionDashboardView.as_view({'get': 'stats'}), name='production-dashboard-stats'),
    path('efficiency-trends/', views.ProductionDashboardView.as_view({'get': 'efficiency_trends'}), name='production-efficiency-trends'),
]

# Production Line specific URLs
production_line_urls = [
    path('<int:pk>/efficiency/', views.ProductionLineViewSet.as_view({'get': 'efficiency'}), name='production-line-efficiency'),
    path('<int:pk>/capacity/', views.ProductionLineViewSet.as_view({'get': 'capacity'}), name='production-line-capacity'),
    path('<int:pk>/work-orders/', views.ProductionLineViewSet.as_view({'get': 'work_orders'}), name='production-line-orders'),
    path('dashboard-stats/', views.ProductionLineViewSet.as_view({'get': 'dashboard_stats'}), name='production-lines-dashboard'),
]

# Equipment specific URLs
equipment_urls = [
    path('<int:pk>/schedule-maintenance/', views.EquipmentViewSet.as_view({'post': 'schedule_maintenance'}), name='equipment-schedule-maintenance'),
]

# Production Plan specific URLs
production_plan_urls = [
    path('<int:pk>/approve/', views.ProductionPlanViewSet.as_view({'post': 'approve'}), name='production-plan-approve'),
]

# Work Order specific URLs
work_order_urls = [
    path('<int:pk>/complete/', views.WorkOrderViewSet.as_view({'post': 'complete'}), name='work-order-complete'),
]

# Bill of Materials specific URLs
bom_urls = [
    path('<int:pk>/cost-analysis/', views.BillOfMaterialsViewSet.as_view({'get': 'cost_analysis'}), name='bom-cost-analysis'),
]

# Production Entry specific URLs
production_entry_urls = [
    path('daily-summary/', views.ProductionEntryViewSet.as_view({'get': 'daily_summary'}), name='production-entry-daily-summary'),
]

# Quality Check specific URLs
quality_check_urls = [
    path('quality-metrics/', views.QualityCheckViewSet.as_view({'get': 'quality_metrics'}), name='quality-metrics'),
]

# Maintenance Schedule specific URLs
maintenance_schedule_urls = [
    path('maintenance-history/', views.MaintenanceScheduleViewSet.as_view({'get': 'maintenance_history'}), name='maintenance-history'),
]

urlpatterns = [
    # Include the router URLs
    path('api/', include(router.urls)),
    
    # Production Dashboard URLs
    path('api/dashboard/', include(production_dashboard_urls)),
    
    # Production Line URLs
    path('api/production-lines/', include(production_line_urls)),
    
    # Equipment URLs
    path('api/equipment/', include(equipment_urls)),
    
    # Production Plan URLs
    path('api/production-plans/', include(production_plan_urls)),
    
    # Work Order URLs
    path('api/work-orders/', include(work_order_urls)),
    
    # Bill of Materials URLs
    path('api/bill-of-materials/', include(bom_urls)),
    
    # Production Entry URLs
    path('api/production-entries/', include(production_entry_urls)),
    
    # Quality Check URLs
    path('api/quality-checks/', include(quality_check_urls)),
    
    # Maintenance Schedule URLs
    path('api/maintenance-schedules/', include(maintenance_schedule_urls)),
]

# URL patterns summary:
# 
# Production Lines:
# - GET /api/production-lines/ - List all production lines
# - POST /api/production-lines/ - Create new production line
# - GET /api/production-lines/{id}/ - Get specific production line
# - PUT /api/production-lines/{id}/ - Update production line
# - DELETE /api/production-lines/{id}/ - Delete production line
# - GET /api/production-lines/{id}/efficiency/ - Get efficiency metrics
# - GET /api/production-lines/{id}/capacity/ - Get capacity metrics
# - GET /api/production-lines/{id}/work-orders/ - Get work orders for production line
# - GET /api/production-lines/dashboard-stats/ - Get dashboard statistics
# 
# Equipment:
# - GET /api/equipment/ - List all equipment
# - POST /api/equipment/ - Create new equipment
# - GET /api/equipment/{id}/ - Get specific equipment
# - PUT /api/equipment/{id}/ - Update equipment
# - DELETE /api/equipment/{id}/ - Delete equipment
# - POST /api/equipment/{id}/schedule-maintenance/ - Schedule maintenance
# 
# Production Plans:
# - GET /api/production-plans/ - List all production plans
# - POST /api/production-plans/ - Create new production plan
# - GET /api/production-plans/{id}/ - Get specific production plan
# - PUT /api/production-plans/{id}/ - Update production plan
# - DELETE /api/production-plans/{id}/ - Delete production plan
# - POST /api/production-plans/{id}/approve/ - Approve production plan
# 
# Work Orders:
# - GET /api/work-orders/ - List all work orders
# - POST /api/work-orders/ - Create new work order
# - GET /api/work-orders/{id}/ - Get specific work order
# - PUT /api/work-orders/{id}/ - Update work order
# - DELETE /api/work-orders/{id}/ - Delete work order
# - POST /api/work-orders/{id}/complete/ - Complete work order
# 
# Bill of Materials:
# - GET /api/bill-of-materials/ - List all BOMs
# - POST /api/bill-of-materials/ - Create new BOM
# - GET /api/bill-of-materials/{id}/ - Get specific BOM
# - PUT /api/bill-of-materials/{id}/ - Update BOM
# - DELETE /api/bill-of-materials/{id}/ - Delete BOM
# - GET /api/bill-of-materials/{id}/cost-analysis/ - Get cost analysis
# 
# Production Entries:
# - GET /api/production-entries/ - List all production entries
# - POST /api/production-entries/ - Create new production entry
# - GET /api/production-entries/{id}/ - Get specific production entry
# - PUT /api/production-entries/{id}/ - Update production entry
# - DELETE /api/production-entries/{id}/ - Delete production entry
# - GET /api/production-entries/daily-summary/ - Get daily summary
# 
# Quality Checks:
# - GET /api/quality-checks/ - List all quality checks
# - POST /api/quality-checks/ - Create new quality check
# - GET /api/quality-checks/{id}/ - Get specific quality check
# - PUT /api/quality-checks/{id}/ - Update quality check
# - DELETE /api/quality-checks/{id}/ - Delete quality check
# - GET /api/quality-checks/quality-metrics/ - Get quality metrics
# 
# Maintenance Schedules:
# - GET /api/maintenance-schedules/ - List all maintenance schedules
# - POST /api/maintenance-schedules/ - Create new maintenance schedule
# - GET /api/maintenance-schedules/{id}/ - Get specific maintenance schedule
# - PUT /api/maintenance-schedules/{id}/ - Update maintenance schedule
# - DELETE /api/maintenance-schedules/{id}/ - Delete maintenance schedule
# - GET /api/maintenance-schedules/maintenance-history/ - Get maintenance history
# 
# Production Reports:
# - GET /api/production-reports/ - List all production reports
# - POST /api/production-reports/ - Create new production report
# - GET /api/production-reports/{id}/ - Get specific production report
# - PUT /api/production-reports/{id}/ - Update production report
# - DELETE /api/production-reports/{id}/ - Delete production report
# 
# Production Dashboard:
# - GET /api/dashboard/stats/ - Get dashboard statistics
# - GET /api/dashboard/efficiency-trends/ - Get efficiency trends