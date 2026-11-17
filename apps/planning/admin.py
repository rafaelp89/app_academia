from django.contrib import admin
from .models import AnnualPlan, PeriodizationPhase, PlanAdjustmentLog

class PeriodizationPhaseInline(admin.TabularInline):
    model = PeriodizationPhase
    extra = 0

@admin.register(AnnualPlan)
class AnnualPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('is_active', 'start_date')
    search_fields = ('title', 'user__username')
    inlines = [PeriodizationPhaseInline]

@admin.register(PeriodizationPhase)
class PeriodizationPhaseAdmin(admin.ModelAdmin):
    list_display = ('phase_number', 'name', 'annual_plan', 'start_date', 'end_date', 'is_current', 'is_completed')
    list_filter = ('is_current', 'is_completed')

@admin.register(PlanAdjustmentLog)
class PlanAdjustmentLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'action_type', 'reason', 'annual_plan', 'created_at')
    list_filter = ('action_type', 'date')
    search_fields = ('reason', 'explanation')

