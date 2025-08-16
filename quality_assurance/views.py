from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db.models import Count, Avg
from .models import QualityStandard, QualityInspection, QualityAlert, QualityMetrics
from .serializers import (
    QualityStandardSerializer,
    QualityInspectionSerializer,
    QualityAlertSerializer,
    QualityMetricsSerializer
)

class QualityStandardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing quality standards
    """
    queryset = QualityStandard.objects.all()
    serializer_class = QualityStandardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']

class QualityInspectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing quality inspections
    """
    queryset = QualityInspection.objects.all()
    serializer_class = QualityInspectionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'inspector', 'standard']
    search_fields = ['notes']
    ordering_fields = ['inspection_date', 'created_at']
    ordering = ['-inspection_date']

    @action(detail=False, methods=['get'])
    def pending_inspections(self, request):
        """
        Get all pending quality inspections
        """
        pending = self.queryset.filter(status='pending')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def inspection_summary(self, request):
        """
        Get quality inspection summary statistics
        """
        total_inspections = self.queryset.count()
        passed_inspections = self.queryset.filter(status='passed').count()
        failed_inspections = self.queryset.filter(status='failed').count()
        pending_inspections = self.queryset.filter(status='pending').count()
        
        pass_rate = (passed_inspections / total_inspections * 100) if total_inspections > 0 else 0
        
        return Response({
            'total_inspections': total_inspections,
            'passed_inspections': passed_inspections,
            'failed_inspections': failed_inspections,
            'pending_inspections': pending_inspections,
            'pass_rate': round(pass_rate, 2)
        })

class QualityAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing quality alerts
    """
    queryset = QualityAlert.objects.all()
    serializer_class = QualityAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['severity', 'is_resolved']
    search_fields = ['message']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Resolve a quality alert
        """
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active_alerts(self, request):
        """
        Get all active (unresolved) quality alerts
        """
        active = self.queryset.filter(is_resolved=False)
        serializer = self.get_serializer(active, many=True)
        return Response(serializer.data)

class QualityMetricsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing quality metrics
    """
    queryset = QualityMetrics.objects.all()
    serializer_class = QualityMetricsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['metric_type']
    search_fields = ['metric_name']
    ordering_fields = ['recorded_at', 'metric_value']
    ordering = ['-recorded_at']

    @action(detail=False, methods=['get'])
    def quality_trends(self, request):
        """
        Get quality trends over time
        """
        metrics = self.queryset.values('metric_type').annotate(
            avg_value=Avg('metric_value'),
            count=Count('id')
        )
        
        return Response(list(metrics))