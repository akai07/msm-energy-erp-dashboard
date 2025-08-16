from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Company, Department, UserProfile, Notification, SystemConfiguration
from .serializers import (
    CompanySerializer, DepartmentSerializer, UserProfileSerializer,
    NotificationSerializer, SystemConfigurationSerializer, UserSerializer
)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.filter(is_active=True)
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'registration_number', 'city']
    filterset_fields = ['state', 'country']
    ordering = ['name']


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'code']
    ordering = ['code']


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.filter(is_active=True)
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['employee_id', 'user__username', 'user__first_name', 'user__last_name']
    filterset_fields = ['department', 'designation']
    ordering = ['employee_id']


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['notification_type', 'priority', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user, is_active=True)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'notification marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(
            is_read=True, 
            read_at=timezone.now()
        )
        return Response({'status': 'all notifications marked as read'})


class SystemConfigurationViewSet(viewsets.ModelViewSet):
    queryset = SystemConfiguration.objects.filter(is_active=True)
    serializer_class = SystemConfigurationSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['key', 'description']
    filterset_fields = ['data_type']
    ordering = ['key']


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get various statistics for the dashboard
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        stats = {
            'total_employees': User.objects.filter(is_active=True).count(),
            'total_departments': Department.objects.filter(is_active=True).count(),
            'unread_notifications': Notification.objects.filter(
                recipient=request.user, 
                is_read=False, 
                is_active=True
            ).count(),
            'recent_activities': self.get_recent_activities(),
            'department_stats': self.get_department_stats(),
        }
        
        return Response(stats)
    
    def get_recent_activities(self):
        # Get recent notifications as activities
        recent_notifications = Notification.objects.filter(
            is_active=True,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        activities = []
        for notification in recent_notifications:
            activities.append({
                'id': notification.id,
                'title': notification.title,
                'type': notification.notification_type,
                'timestamp': notification.created_at,
                'user': notification.recipient.get_full_name() or notification.recipient.username
            })
        
        return activities
    
    def get_department_stats(self):
        # Get employee count by department
        dept_stats = Department.objects.filter(is_active=True).annotate(
            employee_count=Count('userprofile')
        ).values('name', 'employee_count')
        
        return list(dept_stats)


class CurrentUserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(
                id=pk, 
                recipient=request.user, 
                is_active=True
            )
            notification.mark_as_read()
            return Response({'status': 'notification marked as read'})
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        Notification.objects.filter(
            recipient=request.user, 
            is_read=False, 
            is_active=True
        ).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})


# Template-based views for frontend
@login_required
def dashboard_view(request):
    """Main dashboard view with overview metrics"""
    context = {
        'user': request.user,
        'page_title': 'Dashboard Overview'
    }
    return render(request, 'dashboard.html', context)


@login_required
def energy_dashboard_view(request):
    """Energy monitoring dashboard view"""
    context = {
        'user': request.user,
        'page_title': 'Energy Dashboard'
    }
    return render(request, 'energy_dashboard.html', context)


def api_dashboard_data(request):
    """API endpoint for dashboard data"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Sample data - in production, this would fetch real data
    data = {
        'metrics': {
            'total_revenue': 24567890,
            'energy_efficiency': 87.3,
            'active_orders': 156,
            'production_output': 1234
        },
        'energy_consumption': {
            'current': 14567,
            'peak_demand': 18234,
            'efficiency_rating': 87.3,
            'cost_savings': 123456
        },
        'recent_activities': [
            {
                'time': '10:30 AM',
                'activity': 'New purchase order created',
                'module': 'Inventory',
                'status': 'Completed'
            },
            {
                'time': '09:45 AM',
                'activity': 'Quality inspection scheduled',
                'module': 'Quality',
                'status': 'Pending'
            }
        ]
    }
    
    return JsonResponse(data)