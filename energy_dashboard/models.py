from django.db import models
from django.utils import timezone
from core.models import BaseModel
import pandas as pd
from datetime import datetime, timedelta


class EnergyReading(BaseModel):
    """Model to store energy consumption data from Steel_industry_data.csv"""
    timestamp = models.DateTimeField(db_index=True)
    usage_kwh = models.FloatField(help_text="Energy consumption in kWh")
    lagging_current_reactive_power_kvarh = models.FloatField()
    leading_current_reactive_power_kvarh = models.FloatField()
    co2_emissions_tco2 = models.FloatField(help_text="CO2 emissions in tCO2")
    lagging_current_power_factor = models.FloatField()
    leading_current_power_factor = models.FloatField()
    nsm = models.FloatField(help_text="Number of Seconds from Midnight")
    day_of_week = models.CharField(max_length=20)
    load_type = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['day_of_week']),
            models.Index(fields=['load_type']),
        ]
    
    def __str__(self):
        return f"Energy Reading - {self.timestamp} - {self.usage_kwh} kWh"
    
    @classmethod
    def get_daily_consumption(cls, date):
        """Get total energy consumption for a specific date"""
        start_date = datetime.combine(date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        readings = cls.objects.filter(
            timestamp__gte=start_date,
            timestamp__lt=end_date
        )
        
        return {
            'total_kwh': sum(r.usage_kwh for r in readings),
            'total_co2': sum(r.co2_emissions_tco2 for r in readings),
            'avg_power_factor': sum(r.lagging_current_power_factor for r in readings) / len(readings) if readings else 0,
            'reading_count': len(readings)
        }
    
    @classmethod
    def get_hourly_consumption(cls, date):
        """Get hourly energy consumption for a specific date"""
        start_date = datetime.combine(date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        readings = cls.objects.filter(
            timestamp__gte=start_date,
            timestamp__lt=end_date
        ).order_by('timestamp')
        
        hourly_data = {}
        for reading in readings:
            hour = reading.timestamp.hour
            if hour not in hourly_data:
                hourly_data[hour] = {
                    'kwh': 0,
                    'co2': 0,
                    'count': 0
                }
            hourly_data[hour]['kwh'] += reading.usage_kwh
            hourly_data[hour]['co2'] += reading.co2_emissions_tco2
            hourly_data[hour]['count'] += 1
        
        return hourly_data


class EnergyAlert(BaseModel):
    """Model for energy consumption alerts and thresholds"""
    ALERT_TYPES = [
        ('high_consumption', 'High Energy Consumption'),
        ('low_power_factor', 'Low Power Factor'),
        ('peak_demand', 'Peak Demand Alert'),
        ('carbon_threshold', 'Carbon Emission Threshold'),
        ('efficiency_drop', 'Efficiency Drop'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    threshold_value = models.FloatField()
    actual_value = models.FloatField()
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.severity} - {self.created_at}"
    
    def resolve(self, user=None):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()


class EnergyEfficiencyMetric(BaseModel):
    """Model to track energy efficiency metrics over time"""
    date = models.DateField(db_index=True)
    total_energy_kwh = models.FloatField()
    total_co2_emissions = models.FloatField()
    average_power_factor = models.FloatField()
    peak_demand_kw = models.FloatField()
    off_peak_consumption_kwh = models.FloatField()
    peak_consumption_kwh = models.FloatField()
    efficiency_score = models.FloatField(help_text="Calculated efficiency score (0-100)")
    cost_per_kwh = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Energy Metrics - {self.date} - {self.total_energy_kwh} kWh"
    
    def calculate_efficiency_score(self):
        """Calculate efficiency score based on various factors"""
        # Base score starts at 100
        score = 100
        
        # Deduct points for low power factor
        if self.average_power_factor < 0.9:
            score -= (0.9 - self.average_power_factor) * 50
        
        # Deduct points for high CO2 emissions per kWh
        co2_per_kwh = self.total_co2_emissions / self.total_energy_kwh if self.total_energy_kwh > 0 else 0
        if co2_per_kwh > 0.5:  # Threshold for high emissions
            score -= (co2_per_kwh - 0.5) * 20
        
        # Bonus for off-peak usage
        if self.total_energy_kwh > 0:
            off_peak_ratio = self.off_peak_consumption_kwh / self.total_energy_kwh
            if off_peak_ratio > 0.6:  # More than 60% off-peak usage
                score += (off_peak_ratio - 0.6) * 25
        
        self.efficiency_score = max(0, min(100, score))
        return self.efficiency_score


class EnergyTarget(BaseModel):
    """Model for setting energy consumption and efficiency targets"""
    TARGET_TYPES = [
        ('daily_consumption', 'Daily Energy Consumption'),
        ('monthly_consumption', 'Monthly Energy Consumption'),
        ('carbon_emissions', 'Carbon Emissions'),
        ('power_factor', 'Power Factor'),
        ('efficiency_score', 'Efficiency Score'),
        ('cost_reduction', 'Cost Reduction'),
    ]
    
    target_type = models.CharField(max_length=50, choices=TARGET_TYPES)
    target_value = models.FloatField()
    current_value = models.FloatField(default=0)
    target_date = models.DateField()
    description = models.TextField()
    is_achieved = models.BooleanField(default=False)
    achievement_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['target_date']
    
    def __str__(self):
        return f"{self.get_target_type_display()} - Target: {self.target_value} by {self.target_date}"
    
    def check_achievement(self):
        """Check if target has been achieved"""
        if self.target_type in ['daily_consumption', 'monthly_consumption', 'carbon_emissions']:
            # For consumption and emissions, lower is better
            achieved = self.current_value <= self.target_value
        else:
            # For power factor and efficiency, higher is better
            achieved = self.current_value >= self.target_value
        
        if achieved and not self.is_achieved:
            self.is_achieved = True
            self.achievement_date = timezone.now().date()
            self.save()
        
        return achieved
    
    @property
    def progress_percentage(self):
        """Calculate progress towards target as percentage"""
        if self.target_type in ['daily_consumption', 'monthly_consumption', 'carbon_emissions']:
            # For consumption targets, progress is inverse
            if self.target_value == 0:
                return 0
            progress = max(0, (self.target_value - self.current_value) / self.target_value * 100)
        else:
            # For efficiency targets, progress is direct
            if self.target_value == 0:
                return 0
            progress = min(100, self.current_value / self.target_value * 100)
        
        return round(progress, 2)


class EnergyReport(BaseModel):
    """Model for storing generated energy reports"""
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('quarterly', 'Quarterly Report'),
        ('annual', 'Annual Report'),
        ('custom', 'Custom Period Report'),
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    title = models.CharField(max_length=200)
    summary = models.TextField()
    total_energy_kwh = models.FloatField()
    total_co2_emissions = models.FloatField()
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    average_efficiency_score = models.FloatField()
    report_data = models.JSONField(default=dict)  # Store detailed report data
    file_path = models.FileField(upload_to='energy_reports/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"