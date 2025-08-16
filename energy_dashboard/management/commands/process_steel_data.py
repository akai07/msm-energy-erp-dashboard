from django.core.management.base import BaseCommand
from energy_dashboard.data_processor import SteelIndustryDataProcessor
import json

class Command(BaseCommand):
    help = 'Process Steel Industry Energy Data CSV and populate database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the Steel Industry CSV file (optional)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for database operations (default: 1000)',
        )
        parser.add_argument(
            '--show-insights',
            action='store_true',
            help='Display energy insights after processing',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Steel Industry Data Processing...'))
        
        # Initialize processor
        csv_path = options.get('csv_path')
        processor = SteelIndustryDataProcessor(csv_path)
        
        # Process data
        result = processor.process_all()
        
        if result and result.get('success'):
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed {result["records_processed"]} records'
                )
            )
            
            # Display correlations
            self.stdout.write('\n' + self.style.WARNING('Energy Correlations:'))
            correlations = result.get('correlations', {})
            
            if 'usage_co2_correlation' in correlations:
                self.stdout.write(f'  Usage-CO2 Correlation: {correlations["usage_co2_correlation"]:.3f}')
            
            if 'power_factor_efficiency' in correlations:
                self.stdout.write(f'  Power Factor-Efficiency Correlation: {correlations["power_factor_efficiency"]:.3f}')
            
            if 'load_type_usage' in correlations:
                self.stdout.write('\n  Average Usage by Load Type:')
                for load_type, usage in correlations['load_type_usage'].items():
                    self.stdout.write(f'    {load_type}: {usage:.2f} kWh')
            
            if 'peak_hours' in correlations:
                peak_hours = correlations['peak_hours']
                self.stdout.write(f'\n  Peak Usage Hours: {peak_hours}')
            
            # Display insights if requested
            if options['show_insights']:
                insights = result.get('insights', [])
                if insights:
                    self.stdout.write('\n' + self.style.WARNING('Energy Insights:'))
                    for insight in insights:
                        style_map = {
                            'warning': self.style.WARNING,
                            'alert': self.style.ERROR,
                            'info': self.style.SUCCESS,
                            'optimization': self.style.NOTICE
                        }
                        style_func = style_map.get(insight['type'], self.style.SUCCESS)
                        
                        self.stdout.write(f'\n  {style_func(insight["title"])}:')
                        self.stdout.write(f'    {insight["message"]}')
                        self.stdout.write(f'    Recommendation: {insight["recommendation"]}')
            
            self.stdout.write('\n' + self.style.SUCCESS('Data processing completed successfully!'))
        else:
            self.stdout.write(
                self.style.ERROR('Data processing failed. Check logs for details.')
            )
            return
        
        self.stdout.write('\n' + self.style.SUCCESS('You can now view the processed data in the Energy Dashboard.'))