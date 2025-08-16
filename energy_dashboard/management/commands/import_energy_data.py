import csv
import os
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from energy_dashboard.models import EnergyReading, EnergyAlert, EnergyEfficiencyMetric


class Command(BaseCommand):
    help = 'Import energy data from Steel_industry_data.csv'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='Steel_industry_data.csv',
            help='Path to the CSV file (default: Steel_industry_data.csv in project root)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing energy readings before import'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch (default: 1000)'
        )
    
    def handle(self, *args, **options):
        file_path = options['file']
        
        # If file path is relative, make it relative to project root
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR, file_path)
        
        if not os.path.exists(file_path):
            raise CommandError(f'File "{file_path}" does not exist.')
        
        if options['clear']:
            self.stdout.write('Clearing existing energy readings...')
            EnergyReading.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))
        
        self.stdout.write(f'Starting import from {file_path}...')
        
        batch_size = options['batch_size']
        readings_to_create = []
        total_processed = 0
        total_created = 0
        total_skipped = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
                    try:
                        # Parse the datetime
                        timestamp_str = row['date']
                        timestamp = datetime.strptime(timestamp_str, '%d/%m/%Y %H:%M')
                        timestamp = timezone.make_aware(timestamp)
                        
                        # Check if reading already exists
                        if EnergyReading.objects.filter(timestamp=timestamp).exists():
                            total_skipped += 1
                            continue
                        
                        # Parse numeric values
                        usage_kwh = Decimal(str(row['Usage_kWh']))
                        lagging_reactive_power = Decimal(str(row['Lagging_Current_Reactive.Power_kVarh']))
                        leading_reactive_power = Decimal(str(row['Leading_Current_Reactive_Power_kVarh']))
                        co2_emissions = Decimal(str(row['CO2(tCO2)']))
                        lagging_power_factor = Decimal(str(row['Lagging_Current_Power_Factor']))
                        leading_power_factor = Decimal(str(row['Leading_Current_Power_Factor']))
                        nsm = Decimal(str(row['NSM']))
                        
                        # Map load type
                        load_type_mapping = {
                            'Light_Load': 'light',
                            'Medium_Load': 'medium',
                            'Maximum_Load': 'maximum'
                        }
                        load_type = load_type_mapping.get(row['Load_Type'], 'medium')
                        
                        # Map week status
                        week_status = 'weekday' if row['WeekStatus'] == 'Weekday' else 'weekend'
                        
                        # Calculate power factor (use lagging if available, otherwise leading)
                        power_factor = lagging_power_factor if lagging_power_factor > 0 else leading_power_factor
                        
                        # Calculate total reactive power
                        total_reactive_power = lagging_reactive_power + leading_reactive_power
                        
                        # Create EnergyReading object
                        reading = EnergyReading(
                            timestamp=timestamp,
                            energy_consumption=usage_kwh,
                            power_factor=power_factor / 100,  # Convert percentage to decimal
                            reactive_power=total_reactive_power,
                            co2_emissions=co2_emissions,
                            load_type=load_type,
                            week_status=week_status,
                            day_of_week=row['Day_of_week'].lower(),
                            nsm=nsm,
                            lagging_reactive_power=lagging_reactive_power,
                            leading_reactive_power=leading_reactive_power,
                            lagging_power_factor=lagging_power_factor / 100,
                            leading_power_factor=leading_power_factor / 100
                        )
                        
                        readings_to_create.append(reading)
                        total_processed += 1
                        
                        # Bulk create when batch size is reached
                        if len(readings_to_create) >= batch_size:
                            EnergyReading.objects.bulk_create(readings_to_create)
                            total_created += len(readings_to_create)
                            readings_to_create = []
                            
                            self.stdout.write(
                                f'Processed {total_processed} records, '
                                f'created {total_created}, skipped {total_skipped}'
                            )
                    
                    except (ValueError, KeyError) as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Error processing row {row_num}: {e}. Skipping...'
                            )
                        )
                        total_skipped += 1
                        continue
                
                # Create remaining readings
                if readings_to_create:
                    EnergyReading.objects.bulk_create(readings_to_create)
                    total_created += len(readings_to_create)
        
        except Exception as e:
            raise CommandError(f'Error reading file: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed! '
                f'Total processed: {total_processed}, '
                f'Created: {total_created}, '
                f'Skipped: {total_skipped}'
            )
        )
        
        # Generate efficiency metrics after import
        self.stdout.write('Generating efficiency metrics...')
        self.generate_efficiency_metrics()
        
        # Generate alerts for anomalies
        self.stdout.write('Generating energy alerts...')
        self.generate_energy_alerts()
        
        self.stdout.write(self.style.SUCCESS('Data import and processing completed!'))
    
    def generate_efficiency_metrics(self):
        """Generate daily efficiency metrics from energy readings"""
        from django.db.models import Avg, Sum, Count
        from datetime import date, timedelta
        
        # Get date range from readings
        first_reading = EnergyReading.objects.order_by('timestamp').first()
        last_reading = EnergyReading.objects.order_by('-timestamp').first()
        
        if not first_reading or not last_reading:
            return
        
        current_date = first_reading.timestamp.date()
        end_date = last_reading.timestamp.date()
        
        metrics_to_create = []
        
        while current_date <= end_date:
            # Get readings for this date
            daily_readings = EnergyReading.objects.filter(
                timestamp__date=current_date
            )
            
            if daily_readings.exists():
                # Calculate daily metrics
                daily_stats = daily_readings.aggregate(
                    avg_consumption=Avg('energy_consumption'),
                    total_consumption=Sum('energy_consumption'),
                    avg_power_factor=Avg('power_factor'),
                    total_co2=Sum('co2_emissions'),
                    avg_reactive_power=Avg('reactive_power'),
                    reading_count=Count('id')
                )
                
                # Calculate efficiency score (simplified)
                # Higher power factor and lower reactive power = better efficiency
                power_factor_score = (daily_stats['avg_power_factor'] or 0) * 100
                reactive_power_penalty = min((daily_stats['avg_reactive_power'] or 0) / 10, 20)
                efficiency_score = max(power_factor_score - reactive_power_penalty, 0)
                
                # Determine efficiency rating
                if efficiency_score >= 90:
                    efficiency_rating = 'excellent'
                elif efficiency_score >= 80:
                    efficiency_rating = 'good'
                elif efficiency_score >= 70:
                    efficiency_rating = 'fair'
                else:
                    efficiency_rating = 'poor'
                
                metric = EnergyEfficiencyMetric(
                    date=current_date,
                    efficiency_score=Decimal(str(round(efficiency_score, 2))),
                    efficiency_rating=efficiency_rating,
                    total_consumption=daily_stats['total_consumption'] or Decimal('0'),
                    average_power_factor=daily_stats['avg_power_factor'] or Decimal('0'),
                    total_co2_emissions=daily_stats['total_co2'] or Decimal('0'),
                    cost_savings=Decimal('0'),  # Could be calculated based on efficiency improvements
                    recommendations='Optimize power factor and reduce reactive power consumption.'
                )
                
                metrics_to_create.append(metric)
                
                # Bulk create every 30 days
                if len(metrics_to_create) >= 30:
                    EnergyEfficiencyMetric.objects.bulk_create(
                        metrics_to_create, ignore_conflicts=True
                    )
                    metrics_to_create = []
            
            current_date += timedelta(days=1)
        
        # Create remaining metrics
        if metrics_to_create:
            EnergyEfficiencyMetric.objects.bulk_create(
                metrics_to_create, ignore_conflicts=True
            )
        
        self.stdout.write(self.style.SUCCESS('Efficiency metrics generated.'))
    
    def generate_energy_alerts(self):
        """Generate alerts for energy consumption anomalies"""
        from django.db.models import Avg, Q
        from datetime import timedelta
        
        # Calculate average consumption for baseline
        avg_consumption = EnergyReading.objects.aggregate(
            avg=Avg('energy_consumption')
        )['avg'] or Decimal('0')
        
        # Define thresholds
        high_consumption_threshold = avg_consumption * Decimal('2.0')  # 200% of average
        low_power_factor_threshold = Decimal('0.7')  # 70%
        high_co2_threshold = Decimal('0.1')  # 0.1 tCO2
        
        alerts_to_create = []
        
        # Find high consumption readings
        high_consumption_readings = EnergyReading.objects.filter(
            energy_consumption__gt=high_consumption_threshold
        ).order_by('-timestamp')[:100]  # Limit to recent 100
        
        for reading in high_consumption_readings:
            if not EnergyAlert.objects.filter(
                alert_type='high_consumption',
                timestamp=reading.timestamp
            ).exists():
                alert = EnergyAlert(
                    alert_type='high_consumption',
                    severity='high',
                    message=f'High energy consumption detected: {reading.energy_consumption} kWh',
                    timestamp=reading.timestamp,
                    energy_reading=reading,
                    threshold_value=high_consumption_threshold,
                    actual_value=reading.energy_consumption,
                    is_acknowledged=False
                )
                alerts_to_create.append(alert)
        
        # Find low power factor readings
        low_pf_readings = EnergyReading.objects.filter(
            power_factor__lt=low_power_factor_threshold
        ).order_by('-timestamp')[:100]
        
        for reading in low_pf_readings:
            if not EnergyAlert.objects.filter(
                alert_type='low_power_factor',
                timestamp=reading.timestamp
            ).exists():
                alert = EnergyAlert(
                    alert_type='low_power_factor',
                    severity='medium',
                    message=f'Low power factor detected: {reading.power_factor:.2f}',
                    timestamp=reading.timestamp,
                    energy_reading=reading,
                    threshold_value=low_power_factor_threshold,
                    actual_value=reading.power_factor,
                    is_acknowledged=False
                )
                alerts_to_create.append(alert)
        
        # Find high CO2 emissions
        high_co2_readings = EnergyReading.objects.filter(
            co2_emissions__gt=high_co2_threshold
        ).order_by('-timestamp')[:50]
        
        for reading in high_co2_readings:
            if not EnergyAlert.objects.filter(
                alert_type='high_emissions',
                timestamp=reading.timestamp
            ).exists():
                alert = EnergyAlert(
                    alert_type='high_emissions',
                    severity='high',
                    message=f'High CO2 emissions detected: {reading.co2_emissions} tCO2',
                    timestamp=reading.timestamp,
                    energy_reading=reading,
                    threshold_value=high_co2_threshold,
                    actual_value=reading.co2_emissions,
                    is_acknowledged=False
                )
                alerts_to_create.append(alert)
        
        # Bulk create alerts
        if alerts_to_create:
            EnergyAlert.objects.bulk_create(alerts_to_create, ignore_conflicts=True)
            self.stdout.write(
                self.style.SUCCESS(f'Generated {len(alerts_to_create)} energy alerts.')
            )
        else:
            self.stdout.write('No new alerts generated.')