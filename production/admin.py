from django.contrib import admin
from .models import (
    ProductionLine, Equipment, ProductionPlan, WorkOrder,
    BillOfMaterials, ProductionEntry, QualityCheck,
    MaintenanceSchedule, ProductionReport
)


@admin.register(ProductionLine)
class ProductionLineAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'capacity_per_hour', 'efficiency_percentage',
        'supervisor', 'location', 'is_operational', 'created_at'
    )
    list_filter = ('is_operational', 'location', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description')
        }),
        ('Capacity & Performance', {
            'fields': ('capacity_per_hour', 'efficiency_percentage')
        }),
        ('Management', {
            'fields': ('supervisor', 'location', 'is_operational')
        }),
        ('Maintenance', {
            'fields': ('installation_date', 'last_maintenance_date', 'next_maintenance_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'equipment_id', 'name', 'equipment_type', 'production_line',
        'current_status', 'operator', 'location'
    )
    list_filter = ('equipment_type', 'current_status', 'production_line', 'manufacturer')
    search_fields = ('equipment_id', 'name', 'serial_number', 'model_number')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('equipment_id', 'name', 'equipment_type', 'production_line')
        }),
        ('Technical Details', {
            'fields': ('manufacturer', 'model_number', 'serial_number', 'specifications')
        }),
        ('Status & Operation', {
            'fields': ('current_status', 'operator', 'location')
        }),
        ('Purchase Information', {
            'fields': ('purchase_date', 'purchase_cost')
        }),
        ('Maintenance', {
            'fields': ('maintenance_schedule_days', 'last_maintenance_date', 'next_maintenance_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ProductionPlan)
class ProductionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'plan_number', 'plan_name', 'start_date', 'end_date',
        'status', 'planner', 'completion_percentage'
    )
    list_filter = ('status', 'planner', 'plan_date')
    search_fields = ('plan_number', 'plan_name')
    readonly_fields = ('completion_percentage', 'created_at', 'updated_at')
    date_hierarchy = 'plan_date'
    fieldsets = (
        ('Plan Information', {
            'fields': ('plan_number', 'plan_name', 'planner')
        }),
        ('Scheduling', {
            'fields': ('plan_date', 'start_date', 'end_date', 'status')
        }),
        ('Production Quantities', {
            'fields': ('total_planned_quantity', 'total_produced_quantity', 'completion_percentage')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        'wo_number', 'product', 'production_line', 'planned_quantity',
        'produced_quantity', 'status', 'priority', 'start_date'
    )
    list_filter = ('status', 'priority', 'production_line', 'shift')
    search_fields = ('wo_number', 'product__name')
    readonly_fields = ('completion_percentage', 'yield_percentage', 'is_delayed', 'created_at', 'updated_at')
    date_hierarchy = 'start_date'
    fieldsets = (
        ('Work Order Information', {
            'fields': ('wo_number', 'production_plan', 'sales_order', 'product')
        }),
        ('Production Details', {
            'fields': ('production_line', 'planned_quantity', 'produced_quantity', 'rejected_quantity')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date', 'actual_start_date', 'actual_end_date')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'supervisor', 'shift')
        }),
        ('Instructions', {
            'fields': ('instructions', 'quality_requirements')
        }),
        ('Performance Metrics', {
            'fields': ('completion_percentage', 'yield_percentage', 'is_delayed'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'material', 'quantity_required', 'unit_of_measure',
        'wastage_percentage', 'is_critical', 'sequence_number'
    )
    list_filter = ('is_critical', 'unit_of_measure')
    search_fields = ('product__name', 'material__name')
    readonly_fields = ('total_required_with_wastage', 'created_at', 'updated_at')
    fieldsets = (
        ('Product & Material', {
            'fields': ('product', 'material', 'sequence_number')
        }),
        ('Quantity Requirements', {
            'fields': ('quantity_required', 'unit_of_measure', 'wastage_percentage', 'total_required_with_wastage')
        }),
        ('Properties', {
            'fields': ('is_critical', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ProductionEntry)
class ProductionEntryAdmin(admin.ModelAdmin):
    list_display = (
        'work_order', 'entry_date', 'entry_type', 'material',
        'quantity', 'operator', 'shift', 'quality_grade'
    )
    list_filter = ('entry_type', 'shift', 'quality_grade', 'entry_date')
    search_fields = ('work_order__wo_number', 'material__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'entry_date'
    fieldsets = (
        ('Entry Information', {
            'fields': ('work_order', 'entry_date', 'entry_type')
        }),
        ('Production Details', {
            'fields': ('material', 'quantity', 'quality_grade')
        }),
        ('Shift & Operator', {
            'fields': ('operator', 'shift')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(QualityCheck)
class QualityCheckAdmin(admin.ModelAdmin):
    list_display = (
        'check_number', 'material', 'check_type', 'check_date',
        'inspector', 'status', 'pass_percentage'
    )
    list_filter = ('check_type', 'status', 'inspector', 'check_date')
    search_fields = ('check_number', 'material__name')
    readonly_fields = ('pass_percentage', 'created_at', 'updated_at')
    date_hierarchy = 'check_date'
    fieldsets = (
        ('Check Information', {
            'fields': ('check_number', 'work_order', 'material', 'check_type')
        }),
        ('Inspection Details', {
            'fields': ('check_date', 'inspector', 'status')
        }),
        ('Quantities', {
            'fields': ('quantity_checked', 'quantity_passed', 'quantity_failed', 'pass_percentage')
        }),
        ('Test Information', {
            'fields': ('test_parameters', 'test_results', 'defects_found', 'corrective_action')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'maintenance_id', 'equipment', 'maintenance_type', 'scheduled_date',
        'status', 'technician', 'estimated_duration_hours'
    )
    list_filter = ('maintenance_type', 'status', 'technician', 'scheduled_date')
    search_fields = ('maintenance_id', 'equipment__name')
    readonly_fields = ('actual_duration_hours', 'is_overdue', 'created_at', 'updated_at')
    date_hierarchy = 'scheduled_date'
    fieldsets = (
        ('Maintenance Information', {
            'fields': ('maintenance_id', 'equipment', 'maintenance_type', 'technician')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'estimated_duration_hours', 'actual_start_date', 'actual_end_date')
        }),
        ('Status & Progress', {
            'fields': ('status', 'actual_duration_hours', 'is_overdue')
        }),
        ('Work Details', {
            'fields': ('description', 'work_performed', 'parts_used')
        }),
        ('Cost & Follow-up', {
            'fields': ('cost', 'next_maintenance_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ProductionReport)
class ProductionReportAdmin(admin.ModelAdmin):
    list_display = (
        'report_number', 'report_type', 'report_date', 'production_line',
        'supervisor', 'efficiency_percentage', 'quality_percentage'
    )
    list_filter = ('report_type', 'production_line', 'shift', 'report_date')
    search_fields = ('report_number', 'production_line__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'report_date'
    fieldsets = (
        ('Report Information', {
            'fields': ('report_number', 'report_type', 'report_date', 'production_line')
        }),
        ('Shift & Supervision', {
            'fields': ('shift', 'supervisor')
        }),
        ('Production Metrics', {
            'fields': ('planned_production', 'actual_production', 'rejected_quantity')
        }),
        ('Performance Metrics', {
            'fields': ('efficiency_percentage', 'quality_percentage', 'downtime_hours')
        }),
        ('Resource Consumption', {
            'fields': ('energy_consumed', 'material_consumed')
        }),
        ('Issues & Remarks', {
            'fields': ('issues_faced', 'remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )