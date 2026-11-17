import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from apps.planning.models import AnnualPlan, PeriodizationPhase
from apps.planning.services import PlanningService
from apps.training.models import Exercise, WorkoutTemplate

@pytest.mark.django_db
class TestPlanningAndPeriodization:
    def test_annual_plan_creation_12_months(self):
        user = User.objects.create_user(username='aluno_teste', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        assert plan.is_active is True
        assert (plan.end_date - plan.start_date).days >= 365
        assert plan.phases.count() == 5

        # Verifica se as 5 fases cobrem os 12 meses
        phases = list(plan.phases.order_by('phase_number'))
        assert phases[0].phase_number == 1
        assert phases[0].is_current is True
        assert phases[4].phase_number == 5

    def test_workouts_scheduled_only_mon_wed_fri(self):
        user = User.objects.create_user(username='aluno_cal', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        scheduled = plan.scheduled_workouts.all()
        assert scheduled.count() > 150 # ~52 semanas x 3 treinos

        valid_weekdays = {0, 2, 4} # 0=Segunda, 2=Quarta, 4=Sexta
        for w in scheduled:
            assert w.scheduled_date.weekday() in valid_weekdays
            assert w.session_code in ['A', 'B', 'C']

    def test_lower_body_exercises_strictly_conventional_machines(self):
        """Verifica obrigatoriedade de exercícios de pernas serem estritamente máquinas convencionais."""
        PlanningService.seed_initial_data()
        template_b = WorkoutTemplate.objects.get(code='B')

        for item in template_b.template_exercises.all():
            ex = item.exercise
            # Todo exercício do treino de pernas (Treino B) deve ser máquina convencional
            assert ex.is_lower_body_machine is True
            assert ex.load_unit_type in ['MAQUINA_PLACAS', 'MAQUINA_ANILHAS']
            # Não pode conter agachamentos livres ou com barra
            assert 'agachamento livre' not in ex.name.lower()
            assert 'barra livre' not in ex.name.lower()

    def test_load_ranges_prescribed_without_1rm_dogma(self):
        """Verifica prescrição de cargas estimadas com mínimo e máximo válidos."""
        user = User.objects.create_user(username='aluno_cargas', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        first_workout = plan.scheduled_workouts.first()
        for rec in first_workout.exercise_records.all():
            assert rec.load_min_kg > 0
            assert rec.load_max_kg >= rec.load_min_kg
            assert rec.prescribed_sets >= 3
            assert rec.rest_seconds >= 60

