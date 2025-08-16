from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    EnergyReading, EnergyAlert, EnergyEfficiencyMetric,
    EnergyTarget, EnergyReport
)


class EnergyReadingSerializer(serializers.ModelSerializer):
    """Serializer for Energy Reading data"""
    
    class Meta:
        model = EnergyReading
        fields = [
            'id', 'timestamp', 'usage_kwh', 'lagging_current_reactive_power_kvarh',
            'leading_current_reactive_power_kvarh', 'co2_kg', 'load_type',
            'notes', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EnergyReadingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Energy Reading data from CSV"""
    
    class Meta:
        model = EnergyReading
        fields = [
            'timestamp', 'usage_kwh', 'lagging_current_reactive_power_kvarh',
            'leading_current_reactive_power_kvarh', 'co2_kg', 'load_type', 'notes'
        ]


class EnergyAlertSerializer(serializers.ModelSerializer):
    """Serializer for Energy Alerts"""
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.get_full_name', read_only=True)
    
    class Meta:
        model = EnergyAlert
        fields = [
            'id', 'alert_type', 'threshold_value', 'current_value',
            'severity', 'message', 'is_triggered', 'triggered_at',
            'acknowledged_by', 'acknowledged_by_name', 'acknowledged_at',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'triggered_at']


class EnergyEfficiencyMetricSerializer(serializers.ModelSerializer):
    """Serializer for Energy Efficiency Metrics"""
    
    class Meta:
        model = EnergyEfficiencyMetric
        fields = [
            'id', 'date', 'total_energy_consumed', 'total_production_output',
            'efficiency_ratio', 'cost_per_unit', 'carbon_footprint',
            'notes', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'efficiency_ratio']


class EnergyTargetSerializer(serializers.ModelSerializer):
    """Serializer for Energy Targets"""
    
    class Meta:
        model = EnergyTarget
        fields = [
            'id', 'name', 'target_type', 'target_value', 'current_value',
            'start_date', 'end_date', 'description', 'achievement_percentage',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'achievement_percentage']


class EnergyReportSerializer(serializers.ModelSerializer):
    """Serializer for Energy Reports"""
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    
    class Meta:
        model = EnergyReport
        fields = [
            'id', 'name', 'report_type', 'start_date', 'end_date',
            'report_data', 'summary', 'generated_date', 'generated_by',
            'generated_by_name', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'generated_date']


class EnergyDashboardStatsSerializer(serializers.Serializer):
    """Serializer for Energy Dashboard Statistics"""
    total_energy_consumption = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_co2_emissions = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_efficiency = serializers.DecimalField(max_digits=5, decimal_places=2)
    active_alerts_count = serializers.IntegerField()
    energy_cost_today = serializers.DecimalField(max_digits=15, decimal_places=2)
    energy_savings_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    peak_usage_time = serializers.DateTimeField()
    current_load_type = serializers.CharField()
    
    # Trend data
    hourly_consumption = serializers.ListField(child=serializers.DictField())
    daily_consumption = serializers.ListField(child=serializers.DictField())
    monthly_consumption = serializers.ListField(child=serializers.DictField())
    
    # Efficiency trends
    efficiency_trend = serializers.ListField(child=serializers.DictField())
    
    # Alert summary
    alert_summary = serializers.DictField()
    
    # Target progress
    target_progress = serializers.ListField(child=serializers.DictField())


class EnergyConsumptionTrendSerializer(serializers.Serializer):
    """Serializer for Energy Consumption Trends"""
    period = serializers.CharField()  # 'hourly', 'daily', 'weekly', 'monthly'
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    data_points = serializers.ListField(child=serializers.DictField())
    total_consumption = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_consumption = serializers.DecimalField(max_digits=15, decimal_places=2)
    peak_consumption = serializers.DecimalField(max_digits=15, decimal_places=2)
    peak_time = serializers.DateTimeField()


class EnergyComparisonSerializer(serializers.Serializer):
    """Serializer for Energy Consumption Comparisons"""
    current_period = serializers.DictField()
    previous_period = serializers.DictField()
    percentage_change = serializers.DecimalField(max_digits=5, decimal_places=2)
    trend_direction = serializers.CharField()  # 'up', 'down', 'stable'
    

class CSVUploadSerializer(serializers.Serializer):
    """Serializer for CSV file upload"""
    file = serializers.FileField()
    
    def validate_file(self, value):
        """Validate uploaded file"""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("File must be a CSV file.")
        
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("File size must be less than 10MB.")
        
        return value


class EnergyPredictionSerializer(serializers.Serializer):
    """Serializer for Energy Consumption Predictions"""
    prediction_date = serializers.DateTimeField()
    predicted_consumption = serializers.DecimalField(max_digits=15, decimal_places=2)
    confidence_interval_lower = serializers.DecimalField(max_digits=15, decimal_places=2)
    confidence_interval_upper = serializers.DecimalField(max_digits=15, decimal_places=2)
    prediction_model = serializers.CharField()
    accuracy_score = serializers.DecimalField(max_digits=5, decimal_places=4)


class EnergyOptimizationRecommendationSerializer(serializers.Serializer):
    """Serializer for Energy Optimization Recommendations"""
    recommendation_type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    potential_savings_kwh = serializers.DecimalField(max_digits=15, decimal_places=2)
    potential_savings_cost = serializers.DecimalField(max_digits=15, decimal_places=2)
    implementation_difficulty = serializers.CharField()  # 'easy', 'medium', 'hard'
    estimated_implementation_time = serializers.CharField()
    priority_score = serializers.IntegerField()