import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.conf import settings
import os
from .models import EnergyReading, EnergyAlert, EnergyEfficiencyMetric
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class SteelIndustryDataProcessor:
    """
    Processes Steel Industry Energy Data CSV and creates energy correlations
    """
    
    def __init__(self, csv_file_path=None):
        if csv_file_path is None:
            self.csv_file_path = os.path.join(settings.BASE_DIR, 'Steel_industry_data.csv')
        else:
            self.csv_file_path = csv_file_path
        self.df = None
        
    def load_data(self):
        """Load CSV data into pandas DataFrame"""
        try:
            self.df = pd.read_csv(self.csv_file_path)
            logger.info(f"Loaded {len(self.df)} records from {self.csv_file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            return False
    
    def clean_data(self):
        """Clean and preprocess the data"""
        if self.df is None:
            return False
            
        try:
            # Convert date column to datetime
            self.df['date'] = pd.to_datetime(self.df['date'], format='%d/%m/%Y %H:%M')
            
            # Handle missing values
            self.df = self.df.fillna(0)
            
            # Create additional time-based features
            self.df['hour'] = self.df['date'].dt.hour
            self.df['month'] = self.df['date'].dt.month
            self.df['year'] = self.df['date'].dt.year
            self.df['quarter'] = self.df['date'].dt.quarter
            
            # Calculate total power consumption
            self.df['Total_Power_kW'] = self.df['Usage_kWh'] * 4  # Convert 15-min intervals to hourly
            
            # Calculate power efficiency metrics
            self.df['Power_Efficiency'] = self.df['Usage_kWh'] / (self.df['Usage_kWh'] + 
                                                                self.df['Lagging_Current_Reactive.Power_kVarh'] + 
                                                                self.df['Leading_Current_Reactive_Power_kVarh'])
            
            # Calculate CO2 intensity
            self.df['CO2_Intensity'] = self.df['CO2(tCO2)'] / self.df['Usage_kWh']
            self.df['CO2_Intensity'] = self.df['CO2_Intensity'].replace([np.inf, -np.inf], 0)
            
            logger.info("Data cleaning completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            return False
    
    def calculate_correlations(self):
        """Calculate energy correlations and insights"""
        if self.df is None:
            return {}
            
        try:
            correlations = {
                'usage_co2_correlation': self.df['Usage_kWh'].corr(self.df['CO2(tCO2)']),
                'power_factor_efficiency': self.df['Lagging_Current_Power_Factor'].corr(self.df['Power_Efficiency']),
                'load_type_usage': self.df.groupby('Load_Type')['Usage_kWh'].mean().to_dict(),
                'weekday_weekend_usage': self.df.groupby('WeekStatus')['Usage_kWh'].mean().to_dict(),
                'hourly_patterns': self.df.groupby('hour')['Usage_kWh'].mean().to_dict(),
                'monthly_trends': self.df.groupby('month')['Usage_kWh'].mean().to_dict(),
                'peak_hours': self.df.groupby('hour')['Usage_kWh'].mean().nlargest(5).index.tolist(),
                'efficiency_by_load': self.df.groupby('Load_Type')['Power_Efficiency'].mean().to_dict(),
                'co2_by_load_type': self.df.groupby('Load_Type')['CO2(tCO2)'].sum().to_dict()
            }
            
            logger.info("Energy correlations calculated successfully")
            return correlations
        except Exception as e:
            logger.error(f"Error calculating correlations: {e}")
            return {}
    
    def get_energy_insights(self):
        """Generate energy insights and recommendations"""
        if self.df is None:
            return []
            
        insights = []
        
        try:
            # Peak usage analysis
            peak_usage = self.df['Usage_kWh'].max()
            avg_usage = self.df['Usage_kWh'].mean()
            
            if peak_usage > avg_usage * 2:
                insights.append({
                    'type': 'warning',
                    'title': 'High Peak Usage Detected',
                    'message': f'Peak usage ({peak_usage:.2f} kWh) is {peak_usage/avg_usage:.1f}x higher than average',
                    'recommendation': 'Consider load balancing during peak hours'
                })
            
            # Power factor analysis
            avg_power_factor = self.df['Lagging_Current_Power_Factor'].mean()
            if avg_power_factor < 80:
                insights.append({
                    'type': 'alert',
                    'title': 'Low Power Factor',
                    'message': f'Average power factor is {avg_power_factor:.1f}%',
                    'recommendation': 'Install power factor correction equipment'
                })
            
            # CO2 emissions analysis
            total_co2 = self.df['CO2(tCO2)'].sum()
            if total_co2 > 1000:
                insights.append({
                    'type': 'info',
                    'title': 'Carbon Footprint Analysis',
                    'message': f'Total CO2 emissions: {total_co2:.2f} tCO2',
                    'recommendation': 'Consider renewable energy sources to reduce emissions'
                })
            
            # Load type efficiency
            load_efficiency = self.df.groupby('Load_Type')['Power_Efficiency'].mean()
            least_efficient = load_efficiency.idxmin()
            insights.append({
                'type': 'optimization',
                'title': 'Load Type Optimization',
                'message': f'{least_efficient} load type has lowest efficiency ({load_efficiency[least_efficient]:.3f})',
                'recommendation': f'Optimize {least_efficient} operations for better efficiency'
            })
            
            logger.info(f"Generated {len(insights)} energy insights")
            return insights
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    def save_to_database(self, batch_size=1000):
        """Save processed data to Django models"""
        if self.df is None:
            return False
            
        try:
            # Process data in batches
            total_records = len(self.df)
            created_count = 0
            
            for i in range(0, total_records, batch_size):
                batch_df = self.df.iloc[i:i+batch_size]
                energy_records = []
                
                for _, row in batch_df.iterrows():
                    # Create EnergyReading record
                    energy_record = EnergyReading(
                        timestamp=timezone.make_aware(row['date']),
                        usage_kwh=row['Usage_kWh'],
                        lagging_current_reactive_power_kvarh=row['Lagging_Current_Reactive.Power_kVarh'],
                        leading_current_reactive_power_kvarh=row['Leading_Current_Reactive_Power_kVarh'],
                        co2_emissions_tco2=row['CO2(tCO2)'],
                        lagging_current_power_factor=row['Lagging_Current_Power_Factor'],
                        leading_current_power_factor=row['Leading_Current_Power_Factor'],
                        nsm=row['NSM'],
                        day_of_week=row['Day_of_week'],
                        load_type=row['Load_Type']
                    )
                    energy_records.append(energy_record)
                
                # Bulk create records
                EnergyReading.objects.bulk_create(energy_records, ignore_conflicts=True)
                
                created_count += len(energy_records)
                logger.info(f"Processed batch {i//batch_size + 1}/{(total_records//batch_size) + 1}")
            
            logger.info(f"Successfully saved {created_count} records to database")
            return True
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return False
    
    def process_all(self):
        """Run complete data processing pipeline"""
        logger.info("Starting steel industry data processing...")
        
        if not self.load_data():
            return False
            
        if not self.clean_data():
            return False
            
        correlations = self.calculate_correlations()
        insights = self.get_energy_insights()
        
        # Save to database
        if not self.save_to_database():
            return False
            
        logger.info("Steel industry data processing completed successfully")
        return {
            'success': True,
            'records_processed': len(self.df),
            'correlations': correlations,
            'insights': insights
        }