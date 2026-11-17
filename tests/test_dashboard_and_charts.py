import pytest
from django.contrib.auth.models import User
from apps.planning.services import PlanningService
from apps.dashboard.services import DashboardService

@pytest.mark.django_db
class TestDashboardAndCharts:
    def test_kpi_calculations(self):
        user = User.objects.create_user(username='aluno_kpi', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        kpis = DashboardService.get_kpis(plan)
        assert 'overall_progress_pct' in kpis
        assert 'total_workouts' in kpis
        assert kpis['total_workouts'] > 150
        assert 'current_week_num' in kpis
        assert kpis['current_week_num'] >= 1
        assert 'days_remaining' in kpis
        assert kpis['days_remaining'] <= 366

    def test_matplotlib_server_side_svg_generation(self):
        """Verifica se os gráficos SVG são gerados pelo Matplotlib sem erros."""
        user = User.objects.create_user(username='aluno_svg', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        freq_svg = DashboardService.generate_monthly_frequency_chart_svg(plan)
        assert '<svg' in freq_svg
        assert '</svg>' in freq_svg
        assert 'Frequência de Treinos por Mês' in freq_svg

        weekly_svg = DashboardService.generate_weekly_completion_chart_svg(plan)
        assert '<svg' in weekly_svg
        assert '</svg>' in weekly_svg
        assert 'Evolução do Cumprimento' in weekly_svg

