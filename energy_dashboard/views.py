from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Max, Min, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
import io
import csv
from decimal import Decimal

from .models import (
    EnergyReading, EnergyAlert, EnergyEfficiencyMetric,
    EnergyTarget, EnergyReport
)
from .data_processor import SteelIndustryDataProcessor
from .serializers import (
    EnergyReadingSerializer, EnergyReadingCreateSerializer,
    EnergyAlertSerializer, EnergyEfficiencyMetricSerializer,
    EnergyTargetSerializer, EnergyReportSerializer,
    EnergyDashboardStatsSerializer, EnergyConsumptionTrendSerializer,
    EnergyComparisonSerializer, CSVUploadSerializer,
    EnergyPredictionSerializer, EnergyOptimizationRecommendationSerializer
)


class EnergyReadingViewSet(viewsets.ModelViewSet):
    """ViewSet for Energy Reading data"""
    queryset = EnergyReading.objects.all()
    serializer_class = EnergyReadingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EnergyReading.objects.filter(is_active=True)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Filter by load type
        load_type = self.request.query_params.get('load_type')
        if load_type:
            queryset = queryset.filter(load_type=load_type)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest energy readings"""
        latest_readings = self.get_queryset()[:10]
        serializer = self.get_serializer(latest_readings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get energy consumption summary"""
        queryset = self.get_queryset()
        
        summary = queryset.aggregate(
            total_consumption=Sum('usage_kwh'),
            avg_consumption=Avg('usage_kwh'),
            max_consumption=Max('usage_kwh'),
            min_consumption=Min('usage_kwh'),
            total_co2=Sum('co2_kg'),
            reading_count=Count('id')
        )
        
        return Response(summary)


class EnergyAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for Energy Alerts"""
    queryset = EnergyAlert.objects.all()
    serializer_class = EnergyAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EnergyAlert.objects.filter(is_active=True)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by triggered status
        is_triggered = self.request.query_params.get('is_triggered')
        if is_triggered is not None:
            queryset = queryset.filter(is_triggered=is_triggered.lower() == 'true')
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert"""
        alert = self.get_object()
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active alerts"""
        active_alerts = self.get_queryset().filter(
            is_triggered=True,
            acknowledged_at__isnull=True
        )
        serializer = self.get_serializer(active_alerts, many=True)
        return Response(serializer.data)


class EnergyEfficiencyMetricViewSet(viewsets.ModelViewSet):
    """ViewSet for Energy Efficiency Metrics"""
    queryset = EnergyEfficiencyMetric.objects.all()
    serializer_class = EnergyEfficiencyMetricSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EnergyEfficiencyMetric.objects.filter(is_active=True)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')
    
    @action(detail=False, methods=['get'])
    def trend(self, request):
        """Get efficiency trend data"""
        queryset = self.get_queryset()
        
        trend_data = []
        for metric in queryset:
            trend_data.append({
                'date': metric.date,
                'efficiency_ratio': metric.efficiency_ratio,
                'cost_per_unit': metric.cost_per_unit,
                'carbon_footprint': metric.carbon_footprint
            })
        
        return Response(trend_data)


class EnergyTargetViewSet(viewsets.ModelViewSet):
    """ViewSet for Energy Targets"""
    queryset = EnergyTarget.objects.all()
    serializer_class = EnergyTargetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EnergyTarget.objects.filter(is_active=True)
        
        # Filter by target type
        target_type = self.request.query_params.get('target_type')
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def progress(self, request):
        """Get target progress summary"""
        targets = self.get_queryset()
        
        progress_data = []
        for target in targets:
            progress_data.append({
                'id': target.id,
                'name': target.name,
                'target_type': target.target_type,
                'target_value': target.target_value,
                'current_value': target.current_value,
                'achievement_percentage': target.achievement_percentage,
                'start_date': target.start_date,
                'end_date': target.end_date
            })
        
        return Response(progress_data)


class EnergyReportViewSet(viewsets.ModelViewSet):
    """ViewSet for Energy Reports"""
    queryset = EnergyReport.objects.all()
    serializer_class = EnergyReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EnergyReport.objects.filter(is_active=True)
        
        # Filter by report type
        report_type = self.request.query_params.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        return queryset.order_by('-generated_date')
    
    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)


class EnergyDashboardStatsView(APIView):
    """API view for Energy Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive energy dashboard statistics"""
        now = timezone.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        
        # Basic statistics
        total_consumption = EnergyReading.objects.filter(
            is_active=True
        ).aggregate(total=Sum('usage_kwh'))['total'] or 0
        
        total_co2 = EnergyReading.objects.filter(
            is_active=True
        ).aggregate(total=Sum('co2_kg'))['total'] or 0
        
        # Today's consumption
        today_consumption = EnergyReading.objects.filter(
            timestamp__date=today,
            is_active=True
        ).aggregate(total=Sum('usage_kwh'))['total'] or 0
        
        # Yesterday's consumption for comparison
        yesterday_consumption = EnergyReading.objects.filter(
            timestamp__date=yesterday,
            is_active=True
        ).aggregate(total=Sum('usage_kwh'))['total'] or 0
        
        # Calculate energy savings percentage
        energy_savings_percentage = 0
        if yesterday_consumption > 0:
            energy_savings_percentage = ((yesterday_consumption - today_consumption) / yesterday_consumption) * 100
        
        # Average efficiency
        avg_efficiency = EnergyEfficiencyMetric.objects.filter(
            is_active=True
        ).aggregate(avg=Avg('efficiency_ratio'))['avg'] or 0
        
        # Active alerts count
        active_alerts_count = EnergyAlert.objects.filter(
            is_triggered=True,
            acknowledged_at__isnull=True,
            is_active=True
        ).count()
        
        # Peak usage time (today)
        peak_reading = EnergyReading.objects.filter(
            timestamp__date=today,
            is_active=True
        ).order_by('-usage_kwh').first()
        
        peak_usage_time = peak_reading.timestamp if peak_reading else now
        current_load_type = peak_reading.load_type if peak_reading else 'Unknown'
        
        # Hourly consumption (last 24 hours)
        hourly_data = []
        for i in range(24):
            hour_start = now - timedelta(hours=i+1)
            hour_end = now - timedelta(hours=i)
            
            hour_consumption = EnergyReading.objects.filter(
                timestamp__range=[hour_start, hour_end],
                is_active=True
            ).aggregate(total=Sum('usage_kwh'))['total'] or 0
            
            hourly_data.append({
                'hour': hour_start.strftime('%H:00'),
                'consumption': float(hour_consumption)
            })
        
        # Daily consumption (last 7 days)
        daily_data = []
        for i in range(7):
            day = today - timedelta(days=i)
            day_consumption = EnergyReading.objects.filter(
                timestamp__date=day,
                is_active=True
            ).aggregate(total=Sum('usage_kwh'))['total'] or 0
            
            daily_data.append({
                'date': day.strftime('%Y-%m-%d'),
                'consumption': float(day_consumption)
            })
        
        # Monthly consumption (last 12 months)
        monthly_data = []
        for i in range(12):
            month_start = today.replace(day=1) - timedelta(days=i*30)
            month_end = month_start + timedelta(days=30)
            
            month_consumption = EnergyReading.objects.filter(
                timestamp__date__range=[month_start, month_end],
                is_active=True
            ).aggregate(total=Sum('usage_kwh'))['total'] or 0
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'consumption': float(month_consumption)
            })
        
        # Efficiency trend (last 30 days)
        efficiency_trend = []
        efficiency_metrics = EnergyEfficiencyMetric.objects.filter(
            date__gte=last_month,
            is_active=True
        ).order_by('date')
        
        for metric in efficiency_metrics:
            efficiency_trend.append({
                'date': metric.date.strftime('%Y-%m-%d'),
                'efficiency_ratio': float(metric.efficiency_ratio),
                'cost_per_unit': float(metric.cost_per_unit)
            })
        
        # Alert summary
        alert_summary = {
            'critical': EnergyAlert.objects.filter(
                severity='CRITICAL', is_triggered=True, is_active=True
            ).count(),
            'high': EnergyAlert.objects.filter(
                severity='HIGH', is_triggered=True, is_active=True
            ).count(),
            'medium': EnergyAlert.objects.filter(
                severity='MEDIUM', is_triggered=True, is_active=True
            ).count(),
            'low': EnergyAlert.objects.filter(
                severity='LOW', is_triggered=True, is_active=True
            ).count()
        }
        
        # Target progress
        target_progress = []
        targets = EnergyTarget.objects.filter(is_active=True)
        for target in targets:
            target_progress.append({
                'name': target.name,
                'target_type': target.target_type,
                'achievement_percentage': float(target.achievement_percentage)
            })
        
        # Estimate energy cost (assuming $0.12 per kWh)
        energy_cost_today = float(today_consumption) * 0.12
        
        stats = {
            'total_energy_consumption': float(total_consumption),
            'total_co2_emissions': float(total_co2),
            'average_efficiency': float(avg_efficiency),
            'active_alerts_count': active_alerts_count,
            'energy_cost_today': energy_cost_today,
            'energy_savings_percentage': float(energy_savings_percentage),
            'peak_usage_time': peak_usage_time,
            'current_load_type': current_load_type,
            'hourly_consumption': hourly_data,
            'daily_consumption': daily_data,
            'monthly_consumption': monthly_data,
            'efficiency_trend': efficiency_trend,
            'alert_summary': alert_summary,
            'target_progress': target_progress
        }
        
        serializer = EnergyDashboardStatsSerializer(stats)
        return Response(serializer.data)


class EnergyConsumptionTrendView(APIView):
    """API view for Energy Consumption Trends"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get energy consumption trend data"""
        period = request.query_params.get('period', 'daily')  # hourly, daily, weekly, monthly
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            return Response(
                {'error': 'Invalid date format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = EnergyReading.objects.filter(
            timestamp__range=[start_dt, end_dt],
            is_active=True
        )
        
        # Aggregate data based on period
        data_points = []
        
        if period == 'hourly':
            # Group by hour
            current = start_dt.replace(minute=0, second=0, microsecond=0)
            while current <= end_dt:
                next_hour = current + timedelta(hours=1)
                consumption = queryset.filter(
                    timestamp__range=[current, next_hour]
                ).aggregate(total=Sum('usage_kwh'))['total'] or 0
                
                data_points.append({
                    'timestamp': current.isoformat(),
                    'consumption': float(consumption)
                })
                current = next_hour
        
        elif period == 'daily':
            # Group by day
            current = start_dt.date()
            while current <= end_dt.date():
                consumption = queryset.filter(
                    timestamp__date=current
                ).aggregate(total=Sum('usage_kwh'))['total'] or 0
                
                data_points.append({
                    'date': current.isoformat(),
                    'consumption': float(consumption)
                })
                current += timedelta(days=1)
        
        # Calculate summary statistics
        total_consumption = queryset.aggregate(total=Sum('usage_kwh'))['total'] or 0
        avg_consumption = queryset.aggregate(avg=Avg('usage_kwh'))['avg'] or 0
        max_reading = queryset.order_by('-usage_kwh').first()
        
        peak_consumption = max_reading.usage_kwh if max_reading else 0
        peak_time = max_reading.timestamp if max_reading else start_dt
        
        trend_data = {
            'period': period,
            'start_date': start_dt,
            'end_date': end_dt,
            'data_points': data_points,
            'total_consumption': float(total_consumption),
            'average_consumption': float(avg_consumption),
            'peak_consumption': float(peak_consumption),
            'peak_time': peak_time
        }
        
        serializer = EnergyConsumptionTrendSerializer(trend_data)
        return Response(serializer.data)


class CSVUploadView(APIView):
    """API view for uploading CSV energy data"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Upload and process CSV file"""
        serializer = CSVUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        csv_file = serializer.validated_data['file']
        
        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(decoded_file))
            
            created_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_data, start=1):
                try:
                    # Map CSV columns to model fields
                    energy_data = {
                        'timestamp': datetime.fromisoformat(row.get('date', '').replace('Z', '+00:00')),
                        'usage_kwh': Decimal(row.get('Usage_kWh', 0)),
                        'lagging_current_reactive_power_kvarh': Decimal(row.get('Lagging_Current_Reactive.Power_kVarh', 0)),
                        'leading_current_reactive_power_kvarh': Decimal(row.get('Leading_Current_Reactive_Power_kVarh', 0)),
                        'co2_kg': Decimal(row.get('CO2(tCO2)', 0)) * 1000,  # Convert to kg
                        'load_type': row.get('Load_Type', 'Unknown'),
                        'created_by': request.user
                    }
                    
                    # Create energy reading
                    reading_serializer = EnergyReadingCreateSerializer(data=energy_data)
                    if reading_serializer.is_valid():
                        reading_serializer.save(created_by=request.user)
                        created_count += 1
                    else:
                        errors.append(f"Row {row_num}: {reading_serializer.errors}")
                        
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            response_data = {
                'message': f'Successfully imported {created_count} energy readings',
                'created_count': created_count,
                'errors': errors[:10]  # Limit errors to first 10
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to process CSV file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class EnergyOptimizationView(APIView):
    """API view for Energy Optimization Recommendations"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get energy optimization recommendations"""
        # This is a simplified version - in production, this would use ML algorithms
        recommendations = []
        
        # Analyze recent consumption patterns
        last_week = timezone.now().date() - timedelta(days=7)
        recent_readings = EnergyReading.objects.filter(
            timestamp__date__gte=last_week,
            is_active=True
        )
        
        if recent_readings.exists():
            avg_consumption = recent_readings.aggregate(avg=Avg('usage_kwh'))['avg']
            max_consumption = recent_readings.aggregate(max=Max('usage_kwh'))['max']
            
            # Peak load optimization
            if max_consumption > avg_consumption * 1.5:
                recommendations.append({
                    'recommendation_type': 'PEAK_LOAD_MANAGEMENT',
                    'title': 'Optimize Peak Load Usage',
                    'description': 'Your peak energy consumption is significantly higher than average. Consider load shifting to off-peak hours.',
                    'potential_savings_kwh': float(max_consumption - avg_consumption) * 7,
                    'potential_savings_cost': float(max_consumption - avg_consumption) * 7 * 0.12,
                    'implementation_difficulty': 'medium',
                    'estimated_implementation_time': '2-4 weeks',
                    'priority_score': 8
                })
            
            # Equipment efficiency
            efficiency_metrics = EnergyEfficiencyMetric.objects.filter(
                date__gte=last_week,
                is_active=True
            )
            
            if efficiency_metrics.exists():
                avg_efficiency = efficiency_metrics.aggregate(avg=Avg('efficiency_ratio'))['avg']
                
                if avg_efficiency < 0.8:  # Less than 80% efficiency
                    recommendations.append({
                        'recommendation_type': 'EQUIPMENT_EFFICIENCY',
                        'title': 'Improve Equipment Efficiency',
                        'description': 'Current equipment efficiency is below optimal levels. Consider maintenance or upgrades.',
                        'potential_savings_kwh': float(avg_consumption) * 0.15,
                        'potential_savings_cost': float(avg_consumption) * 0.15 * 0.12,
                        'implementation_difficulty': 'hard',
                        'estimated_implementation_time': '1-3 months',
                        'priority_score': 9
                    })
        
        # Energy monitoring
        recommendations.append({
            'recommendation_type': 'MONITORING_ENHANCEMENT',
            'title': 'Enhanced Energy Monitoring',
            'description': 'Implement real-time energy monitoring for better visibility and control.',
            'potential_savings_kwh': float(avg_consumption) * 0.05 if 'avg_consumption' in locals() else 100,
            'potential_savings_cost': float(avg_consumption) * 0.05 * 0.12 if 'avg_consumption' in locals() else 12,
            'implementation_difficulty': 'easy',
            'estimated_implementation_time': '1-2 weeks',
            'priority_score': 6
        })
        
        # Sort by priority score
        recommendations.sort(key=lambda x: x['priority_score'], reverse=True)
        
        serializer = EnergyOptimizationRecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)


class SteelIndustryDataAPIView(APIView):
    """API endpoint for Steel Industry data processing and analysis"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Process Steel Industry CSV data"""
        try:
            processor = SteelIndustryDataProcessor()
            result = processor.process_all()
            
            if result and result.get('success'):
                return Response({
                    'success': True,
                    'message': f'Successfully processed {result["records_processed"]} records',
                    'correlations': result.get('correlations', {}),
                    'insights': result.get('insights', [])
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Data processing failed'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error processing data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Get processed Steel Industry data correlations"""
        try:
            processor = SteelIndustryDataProcessor()
            
            if processor.load_data() and processor.clean_data():
                correlations = processor.calculate_correlations()
                insights = processor.get_energy_insights()
                
                return Response({
                    'correlations': correlations,
                    'insights': insights,
                    'data_summary': {
                        'total_records': len(processor.df),
                        'date_range': {
                            'start': processor.df['date'].min().isoformat(),
                            'end': processor.df['date'].max().isoformat()
                        },
                        'load_types': processor.df['Load_Type'].unique().tolist(),
                        'avg_usage': processor.df['Usage_kWh'].mean(),
                        'total_co2': processor.df['CO2(tCO2)'].sum()
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to load or process data'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': f'Error retrieving data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EnergyCorrelationAPIView(APIView):
    """API endpoint for energy correlation analysis"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get energy correlations from database records"""
        try:
            # Get date range from query params
            days = int(request.query_params.get('days', 30))
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Query energy reading data
            reading_data = EnergyReading.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date,
                is_active=True
            ).values(
                 'timestamp__hour',
                 'load_type',
                 'usage_kwh',
                 'co2_emissions_tco2',
                 'lagging_current_reactive_power_kvarh',
                 'leading_current_reactive_power_kvarh'
             )
            
            if not reading_data:
                return Response({
                    'message': 'No data available for the specified period',
                    'correlations': {}
                }, status=status.HTTP_200_OK)
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(reading_data)
            
            correlations = {
                'hourly_consumption': df.groupby('timestamp__hour')['usage_kwh'].mean().to_dict(),
                'load_type_consumption': df.groupby('load_type')['usage_kwh'].mean().to_dict(),
                'usage_co2_correlation': df['usage_kwh'].corr(df['co2_emissions_tco2']) if len(df) > 1 else 0,
                'usage_reactive_power_correlation': df['usage_kwh'].corr(df['lagging_current_reactive_power_kvarh']) if len(df) > 1 else 0,
                'peak_hours': df.groupby('timestamp__hour')['usage_kwh'].mean().nlargest(5).index.tolist(),
                'total_consumption': df['usage_kwh'].sum(),
                'total_co2': df['co2_emissions_tco2'].sum(),
                'average_consumption': df['usage_kwh'].mean()
            }
            
            return Response({
                'correlations': correlations,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'record_count': len(df)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Error calculating correlations: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)