import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from apps.planning.services import PlanningService
from apps.planning.models import PlanAdjustmentLog
from apps.progress.models import ScheduledWorkout

@pytest.mark.django_db
class TestBacklogAndProgression:
    def test_reorganize_pending_workouts_preserves_recovery(self):
        user = User.objects.create_user(username='aluno_reorg', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        today = timezone.localdate()
        # Simula uma sessão perdida na segunda-feira
        monday = today - timedelta(days=today.weekday())
        past_workout = ScheduledWorkout.objects.filter(
            annual_plan=plan,
            scheduled_date=monday
        ).first()

        if past_workout and past_workout.scheduled_date < today:
            past_workout.status = 'PENDENTE'
            past_workout.save()

            res = PlanningService.reorganize_pending_workouts(plan)
            assert res['success'] is True

            past_workout.refresh_from_db()
            assert past_workout.status == 'NAO_REALIZADO'
            assert 'recuperação' in past_workout.reorganization_note.lower()

            # Verifica log pedagógico
            log = PlanAdjustmentLog.objects.filter(annual_plan=plan, action_type='REORGANIZACAO').first()
            assert log is not None
            assert 'volume agudo excessivo' in log.explanation

    def test_evaluate_and_advance_phase(self):
        user = User.objects.create_user(username='aluno_fase', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        f1 = plan.phases.get(phase_number=1)
        f2 = plan.phases.get(phase_number=2)

        assert f1.is_current is True
        assert f2.is_current is False

        # Marca treinos suficientes para cumprir critérios (>= 75% da fase de 18 treinos)
        for w in ScheduledWorkout.objects.filter(annual_plan=plan, phase=f1)[:15]:
            w.status = 'CONCLUIDO'
            w.save()

        res = PlanningService.evaluate_and_advance_phase(plan)
        assert res['success'] is True

        f1.refresh_from_db()
        f2.refresh_from_db()
        assert f1.is_current is False
        assert f1.is_completed is True
        assert f2.is_current is True

        log = PlanAdjustmentLog.objects.filter(annual_plan=plan, action_type='FASE_AVANCO').first()
        assert log is not None
