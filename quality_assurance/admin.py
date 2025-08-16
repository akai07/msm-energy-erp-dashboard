from django.contrib import admin
from .models import QualityStandard, QualityInspection, QualityAlert, QualityMetrics

@admin.register(QualityStandard)
class QualityStandardAdmin(admin.ModelAdmin):
    list_display = ('standard_id', 'name', 'standard_type', 'version', 'is_active', 'created_at')
    list_filter = ('standard_type', 'is_active', 'created_at')
    search_fields = ('standard_id', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('standard_id', 'name', 'standard_type', 'version', 'description')
        }),
        ('Standards', {
            'fields': ('test_parameters', 'sampling_plan', 'acceptance_criteria')
        }),
        ('Dates', {
            'fields': ('effective_date', 'review_date', 'approved_by')
        }),
        ('Materials', {
            'fields': ('applicable_materials',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(QualityInspection)
class QualityInspectionAdmin(admin.ModelAdmin):
    list_display = ('inspection_number', 'material', 'inspector', 'status', 'overall_result', 'inspection_date')
    list_filter = ('status', 'overall_result', 'inspection_date')
    search_fields = ('inspection_number', 'inspector__username', 'material__name', 'remarks')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'inspection_date'
    
    fieldsets = (
        ('Inspection Details', {
            'fields': ('inspection_number', 'inspection_plan', 'material', 'inspector', 'inspection_date')
        }),
        ('Batch Information', {
            'fields': ('batch_number', 'lot_number', 'work_order', 'supplier')
        }),
        ('Quantities', {
            'fields': ('quantity_inspected', 'quantity_accepted', 'quantity_rejected')
        }),
        ('Results', {
            'fields': ('status', 'overall_result', 'remarks')
        }),
        ('Corrective Action', {
            'fields': ('corrective_action_required', 'corrective_action')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('material', 'inspector', 'inspection_plan')

@admin.register(QualityAlert)
class QualityAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_id', 'title', 'alert_type', 'priority', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'priority', 'is_resolved', 'is_acknowledged', 'created_at')
    search_fields = ('alert_id', 'title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('alert_id', 'title', 'description', 'alert_type', 'priority')
        }),
        ('Related Objects', {
            'fields': ('related_material', 'related_supplier', 'related_ncr')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'due_date')
        }),
        ('Status', {
            'fields': ('is_acknowledged', 'acknowledged_by', 'acknowledged_date', 'is_resolved', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(QualityMetrics)
class QualityMetricsAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'period_type', 'period_start', 'period_end', 'target_value', 'actual_value', 'variance_percentage']
    list_filter = ['metric_type', 'period_type', 'material', 'supplier', 'production_line']
    search_fields = ['metric_type', 'material__name', 'supplier__name']
    readonly_fields = ['variance', 'variance_percentage', 'created_at', 'updated_at']
    date_hierarchy = 'period_start'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('metric_type', 'period_type', 'period_start', 'period_end')
        }),
        ('Related Objects', {
            'fields': ('material', 'supplier', 'production_line')
        }),
        ('Metrics', {
            'fields': ('target_value', 'actual_value', 'unit_of_measure', 'variance', 'variance_percentage', 'trend')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )