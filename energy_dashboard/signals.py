from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import EnergyReading, EnergyAlert, EnergyEfficiencyMetric
from datetime import timedelta


@receiver(post_save, sender=EnergyReading)
def create_energy_alerts(sender, instance, created, **kwargs):
    """Create energy alerts based on energy reading thresholds"""
    if created:
        # High consumption alert
        if instance.usage_kwh > 1000:  # Threshold for high consumption
            EnergyAlert.objects.get_or_create(
                alert_type='high_consumption',
                severity='high',
                defaults={
                    'message': f'High energy consumption detected: {instance.usage_kwh} kWh',
                    'description': f'Energy usage of {instance.usage_kwh} kWh exceeds normal threshold at {instance.timestamp}',
                    'source_data': {'reading_id': instance.id, 'usage_kwh': instance.usage_kwh},
                    'is_active': True
                }
            )
        
        # Low power factor alert
        if instance.lagging_power_factor < 0.8:  # Threshold for low power factor
            EnergyAlert.objects.get_or_create(
                alert_type='low_power_factor',
                severity='medium',
                defaults={
                    'message': f'Low power factor detected: {instance.lagging_power_factor}',
                    'description': f'Power factor of {instance.lagging_power_factor} is below optimal threshold',
                    'source_data': {'reading_id': instance.id, 'power_factor': instance.lagging_power_factor},
                    'is_active': True
                }
            )
        
        # High CO2 emissions alert
        if instance.co2_emissions > 500:  # Threshold for high CO2
            EnergyAlert.objects.get_or_create(
                alert_type='high_emissions',
                severity='high',
                defaults={
                    'message': f'High CO2 emissions detected: {instance.co2_emissions} tCO2',
                    'description': f'CO2 emissions of {instance.co2_emissions} tCO2 exceed environmental threshold',
                    'source_data': {'reading_id': instance.id, 'co2_emissions': instance.co2_emissions},
                    'is_active': True
                }
            )


@receiver(post_save, sender=EnergyReading)
def update_efficiency_metrics(sender, instance, created, **kwargs):
    """Update efficiency metrics when new energy readings are created"""
    if created:
        # Calculate daily efficiency metrics
        date = instance.timestamp.date()
        
        # Get all readings for the day
        daily_readings = EnergyReading.objects.filter(
            timestamp__date=date
        )
        
        if daily_readings.exists():
            # Calculate metrics
            total_usage = sum(reading.usage_kwh for reading in daily_readings)
            avg_power_factor = sum(reading.lagging_power_factor for reading in daily_readings) / daily_readings.count()
            total_co2 = sum(reading.co2_emissions for reading in daily_readings)
            
            # Calculate efficiency score (0-100)
            efficiency_score = min(100, max(0, 
                (avg_power_factor * 100) - (total_co2 / total_usage * 10) if total_usage > 0 else 0
            ))
            
            # Determine efficiency rating
            if efficiency_score >= 90:
                rating = 'excellent'
            elif efficiency_score >= 80:
                rating = 'good'
            elif efficiency_score >= 70:
                rating = 'fair'
            else:
                rating = 'poor'
            
            # Generate recommendations
            recommendations = []
            if avg_power_factor < 0.9:
                recommendations.append('Install power factor correction equipment')
            if total_co2 / total_usage > 0.5 if total_usage > 0 else False:
                recommendations.append('Consider renewable energy sources')
            if total_usage > 8000:  # Daily threshold
                recommendations.append('Implement energy-saving measures during peak hours')
            
            # Create or update efficiency metric
            EnergyEfficiencyMetric.objects.update_or_create(
                date=date,
                defaults={
                    'efficiency_score': efficiency_score,
                    'energy_consumption': total_usage,
                    'power_factor': avg_power_factor,
                    'co2_emissions': total_co2,
                    'efficiency_rating': rating,
                    'recommendations': recommendations
                }
            )


@receiver(pre_save, sender=EnergyAlert)
def update_alert_timestamps(sender, instance, **kwargs):
    """Update alert timestamps when status changes"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = EnergyAlert.objects.get(pk=instance.pk)
            # If alert is being acknowledged
            if old_instance.is_active and not instance.is_active:
                instance.acknowledged_at = timezone.now()
            # If alert is being reactivated
            elif not old_instance.is_active and instance.is_active:
                instance.acknowledged_at = None
        except EnergyAlert.DoesNotExist:
            pass