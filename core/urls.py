from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'user-profiles', views.UserProfileViewSet)
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'system-config', views.SystemConfigurationViewSet)

app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('user-profile/', views.CurrentUserProfileView.as_view(), name='current-user-profile'),
    path('notifications/mark-read/<uuid:pk>/', views.MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read'),
    
    # Template-based views
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('energy-dashboard/', views.energy_dashboard_view, name='energy-dashboard'),
    path('api/dashboard-data/', views.api_dashboard_data, name='api-dashboard-data'),
]