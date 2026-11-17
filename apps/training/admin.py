from django.contrib import admin
from .models import MuscleGroup, Exercise, WorkoutTemplate, WorkoutTemplateExercise

@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class WorkoutTemplateExerciseInline(admin.TabularInline):
    model = WorkoutTemplateExercise
    extra = 1

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'primary_muscle', 'equipment', 'is_lower_body_machine', 'load_unit_type')
    list_filter = ('primary_muscle', 'is_lower_body_machine', 'load_unit_type')
    search_fields = ('name', 'equipment')

@admin.register(WorkoutTemplate)
class WorkoutTemplateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'day_of_week_label', 'focus_summary')
    inlines = [WorkoutTemplateExerciseInline]

