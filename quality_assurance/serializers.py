from rest_framework import serializers
from .models import QualityStandard, QualityInspection, QualityAlert, QualityMetrics

class QualityStandardSerializer(serializers.ModelSerializer):
    """
    Serializer for QualityStandard model
    """
    class Meta:
        model = QualityStandard
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class QualityInspectionSerializer(serializers.ModelSerializer):
    """
    Serializer for QualityInspection model
    """
    inspector_name = serializers.CharField(source='inspector.get_full_name', read_only=True)
    standard_name = serializers.CharField(source='standard.name', read_only=True)
    
    class Meta:
        model = QualityInspection
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, data):
        """
        Validate inspection data
        """
        if data.get('status') == 'failed' and not data.get('notes'):
            raise serializers.ValidationError(
                "Notes are required when marking an inspection as failed."
            )
        return data

class QualityAlertSerializer(serializers.ModelSerializer):
    """
    Serializer for QualityAlert model
    """
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    
    class Meta:
        model = QualityAlert
        fields = '__all__'
        read_only_fields = ('created_at', 'resolved_at', 'resolved_by')

class QualityMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer for QualityMetrics model
    """
    class Meta:
        model = QualityMetrics
        fields = '__all__'
        read_only_fields = ('recorded_at',)

    def validate_metric_value(self, value):
        """
        Validate metric value is not negative
        """
        if value < 0:
            raise serializers.ValidationError("Metric value cannot be negative.")
        return value

class QualityDashboardSerializer(serializers.Serializer):
    """
    Serializer for quality dashboard data
    """
    total_inspections = serializers.IntegerField()
    passed_inspections = serializers.IntegerField()
    failed_inspections = serializers.IntegerField()
    pending_inspections = serializers.IntegerField()
    pass_rate = serializers.FloatField()
    active_alerts = serializers.IntegerField()
    quality_score = serializers.FloatField()
    
class QualityTrendSerializer(serializers.Serializer):
    """
    Serializer for quality trend data
    """
    date = serializers.DateField()
    pass_rate = serializers.FloatField()
    total_inspections = serializers.IntegerField()
    defect_rate = serializers.FloatField()