from django.contrib import admin
from .models import ScheduledWorkout, WorkoutExerciseRecord, WeeklyProgress

class WorkoutExerciseRecordInline(admin.TabularInline):
    model = WorkoutExerciseRecord
    extra = 0
    fields = ('order', 'exercise', 'prescribed_sets', 'prescribed_reps', 'load_min_kg', 'load_max_kg', 'is_completed', 'completed_at')

@admin.register(ScheduledWorkout)
class ScheduledWorkoutAdmin(admin.ModelAdmin):
    list_display = ('scheduled_date', 'session_code', 'title', 'status', 'completed_at')
    list_filter = ('session_code', 'status', 'scheduled_date')
    search_fields = ('title', 'reorganization_note')
    inlines = [WorkoutExerciseRecordInline]

@admin.register(WorkoutExerciseRecord)
class WorkoutExerciseRecordAdmin(admin.ModelAdmin):
    list_display = ('scheduled_workout', 'order', 'exercise', 'load_min_kg', 'load_max_kg', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'exercise__primary_muscle')
    search_fields = ('exercise__name',)

@admin.register(WeeklyProgress)
class WeeklyProgressAdmin(admin.ModelAdmin):
    list_display = ('year', 'week_number', 'start_date', 'completed_sessions_count', 'planned_sessions_count', 'completion_rate', 'status')
    list_filter = ('year', 'status')

