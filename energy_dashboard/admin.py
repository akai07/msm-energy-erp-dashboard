from django.contrib import admin
from .models import (
    EnergyReading, EnergyAlert, EnergyEfficiencyMetric,
    EnergyTarget, EnergyReport
)


@admin.register(EnergyReading)
class EnergyReadingAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'usage_kwh', 'lagging_current_reactive_power_kvarh',
        'leading_current_reactive_power_kvarh', 'co2_emissions_tco2', 'load_type'
    ]
    list_filter = ['load_type', 'day_of_week', 'timestamp', 'created_at']
    search_fields = ['load_type', 'day_of_week']
    date_hierarchy = 'timestamp'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Energy Data', {
            'fields': (
                'timestamp', 'usage_kwh', 'lagging_current_reactive_power_kvarh',
                'leading_current_reactive_power_kvarh', 'co2_emissions_tco2', 'load_type',
                'lagging_current_power_factor', 'leading_current_power_factor', 'nsm', 'day_of_week'
            )
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        })
    )


@admin.register(EnergyAlert)
class EnergyAlertAdmin(admin.ModelAdmin):
    list_display = [
        'alert_type', 'threshold_value', 'actual_value',
        'severity', 'is_resolved', 'created_at'
    ]
    list_filter = ['alert_type', 'severity', 'is_resolved', 'created_at']
    search_fields = ['message', 'alert_type']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    
    fieldsets = (
        ('Alert Configuration', {
            'fields': (
                'alert_type', 'threshold_value', 'actual_value',
                'severity', 'message'
            )
        }),
        ('Status', {
            'fields': ('is_resolved', 'resolved_at', 'resolved_by')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        })
    )


@admin.register(EnergyEfficiencyMetric)
class EnergyEfficiencyMetricAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_energy_kwh', 'total_co2_emissions',
        'efficiency_score', 'total_cost'
    ]
    list_filter = ['date', 'created_at']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at', 'efficiency_score']
    
    fieldsets = (
        ('Metrics Data', {
            'fields': (
                'date', 'total_energy_kwh', 'total_co2_emissions', 'average_power_factor',
                'peak_demand_kw', 'off_peak_consumption_kwh', 'peak_consumption_kwh',
                'efficiency_score', 'cost_per_kwh', 'total_cost'
            )
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        })
    )


@admin.register(EnergyTarget)
class EnergyTargetAdmin(admin.ModelAdmin):
    list_display = [
        'target_type', 'target_value', 'current_value',
        'target_date', 'is_achieved', 'achievement_date'
    ]
    list_filter = ['target_type', 'target_date', 'is_achieved', 'created_at']
    search_fields = ['description']
    readonly_fields = ['created_at', 'updated_at', 'is_achieved', 'achievement_date']
    
    fieldsets = (
        ('Target Configuration', {
            'fields': (
                'target_type', 'target_value', 'current_value',
                'target_date'
            )
        }),
        ('Details', {
            'fields': ('description', 'is_achieved', 'achievement_date')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        })
    )


@admin.register(EnergyReport)
class EnergyReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'report_type', 'start_date', 'end_date',
        'total_energy_kwh', 'total_cost'
    ]
    list_filter = ['report_type', 'start_date', 'end_date', 'created_at']
    search_fields = ['title', 'summary']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Report Configuration', {
            'fields': (
                'title', 'report_type', 'start_date', 'end_date'
            )
        }),
        ('Report Data', {
            'fields': (
                'summary', 'total_energy_kwh', 'total_co2_emissions',
                'total_cost', 'average_efficiency_score', 'report_data', 'file_path'
            )
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        })
    )