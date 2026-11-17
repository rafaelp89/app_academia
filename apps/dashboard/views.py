from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .services import DashboardService
from apps.planning.models import AnnualPlan
from apps.planning.services import PlanningService

@login_required
def dashboard_index(request):
    """
    Dashboard Principal do Praticante.
    Apresenta KPIs consolidados, progresso anual, semana corrente e gráficos SVG gerados no servidor.
    """
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    if not plan:
        plan = PlanningService.initialize_annual_plan_for_user(request.user)

    kpis = DashboardService.get_kpis(plan)

    context = {
        'plan': plan,
        'kpis': kpis,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def frequency_chart_svg(request):
    """Gera no servidor Python via Matplotlib o gráfico SVG de frequência mensal de treinos."""
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    svg_content = DashboardService.generate_monthly_frequency_chart_svg(plan)
    return HttpResponse(svg_content, content_type='image/svg+xml')


@login_required
def weekly_rate_chart_svg(request):
    """Gera no servidor Python via Matplotlib o gráfico SVG de cumprimento semanal."""
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    svg_content = DashboardService.generate_weekly_completion_chart_svg(plan)
    return HttpResponse(svg_content, content_type='image/svg+xml')

