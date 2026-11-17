import pytest
from django.utils import timezone
from django.contrib.auth.models import User
from django.test import Client
from apps.planning.services import PlanningService
from apps.progress.models import ScheduledWorkout, WorkoutExerciseRecord, WeeklyProgress

@pytest.mark.django_db
class TestChecklistSystem:
    def test_toggle_checkbox_updates_persistence_and_timestamp(self):
        user = User.objects.create_user(username='aluno_check', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        client = Client()
        client.force_login(user)

        workout = plan.scheduled_workouts.first()
        record = workout.exercise_records.first()

        assert record.is_completed is False
        assert record.completed_at is None

        # 1. Marca checkbox
        response = client.post(f"/progress/toggle/{record.id}/", HTTP_HX_REQUEST='true')
        assert response.status_code == 200

        record.refresh_from_db()
        assert record.is_completed is True
        assert record.completed_at is not None

        # 2. Desmarca checkbox
        response = client.post(f"/progress/toggle/{record.id}/", HTTP_HX_REQUEST='true')
        assert response.status_code == 200

        record.refresh_from_db()
        assert record.is_completed is False
        assert record.completed_at is None

    def test_completing_all_exercises_marks_workout_completed(self):
        user = User.objects.create_user(username='aluno_full', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        client = Client()
        client.force_login(user)

        workout = plan.scheduled_workouts.first()
        assert workout.status == 'PENDENTE'

        # Marca todos os exercícios da sessão
        for rec in workout.exercise_records.all():
            client.post(f"/progress/toggle/{rec.id}/", HTTP_HX_REQUEST='true')

        workout.refresh_from_db()
        assert workout.status == 'CONCLUIDO'
        assert workout.completed_at is not None
        assert workout.completion_percentage == 100

        # Verifica atualização do WeeklyProgress
        progress = WeeklyProgress.objects.filter(annual_plan=plan).first()
        assert progress is not None
        assert progress.completed_sessions_count >= 1

