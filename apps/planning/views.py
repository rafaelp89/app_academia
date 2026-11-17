from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AnnualPlan, PeriodizationPhase, PlanAdjustmentLog
from .services import PlanningService

@login_required
def plan_detail(request):
    """Exibição completa do macrociclo anual de 12 meses e suas 5 fases."""
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    if not plan:
        plan = PlanningService.initialize_annual_plan_for_user(request.user)

    phases = plan.phases.all().order_by('phase_number')
    adjustment_logs = plan.adjustment_logs.all()[:5]

    context = {
        'plan': plan,
        'phases': phases,
        'adjustment_logs': adjustment_logs,
    }
    return render(request, 'planning/plan_detail.html', context)


@login_required
def phase_detail(request, pk):
    """Detalhamento técnico, metas e prescrições de uma fase específica."""
    phase = get_object_or_404(PeriodizationPhase, pk=pk, annual_plan__user=request.user)
    return render(request, 'planning/phase_detail.html', {'phase': phase})


@login_required
def adjustment_history(request):
    """Registro pedagógico e transparente de todas as decisões tomadas pelo sistema."""
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    logs = plan.adjustment_logs.all() if plan else []
    return render(request, 'planning/adjustment_history.html', {'logs': logs, 'plan': plan})


@login_required
def reorganize_backlog(request):
    """Executa a reorganização inteligente de sessões pendentes preservando recuperação."""
    if request.method == 'POST':
        plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
        if plan:
            result = PlanningService.reorganize_pending_workouts(plan)
            messages.success(request, result['message'])
        return redirect('progress:weekly_view')
    return redirect('progress:weekly_view')


@login_required
def advance_phase(request):
    """Avalia e avança de fase de forma autônoma baseada em critérios técnicos."""
    if request.method == 'POST':
        plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
        if plan:
            result = PlanningService.evaluate_and_advance_phase(plan)
            if result['success']:
                messages.success(request, result['message'])
            else:
                messages.warning(request, result['message'])
        return redirect('planning:plan_detail')
    return redirect('planning:plan_detail')

