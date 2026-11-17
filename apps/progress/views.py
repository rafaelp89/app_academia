from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse
from .models import ScheduledWorkout, WorkoutExerciseRecord, WeeklyProgress
from .services import ProgressService
from apps.planning.models import AnnualPlan
from apps.planning.services import PlanningService

@login_required
def today_workout(request):
    """
    Localiza a sessão de hoje (se for seg/qua/sex) ou a próxima sessão agendada mais próxima.
    """
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    if not plan:
        plan = PlanningService.initialize_annual_plan_for_user(request.user)

    today = timezone.localdate()
    workout = ScheduledWorkout.objects.filter(annual_plan=plan, scheduled_date=today).first()

    if not workout:
        # Se hoje não for dia de treino ou não houver agendamento para hoje, busca o próximo agendado
        workout = ScheduledWorkout.objects.filter(
            annual_plan=plan,
            scheduled_date__gte=today
        ).order_by('scheduled_date').first()

    if not workout:
        # Se já tiver passado de todas as datas, pega o último
        workout = ScheduledWorkout.objects.filter(annual_plan=plan).order_by('-scheduled_date').first()

    if workout:
        return redirect('progress:workout_session', pk=workout.pk)

    return render(request, 'progress/no_workout.html')


@login_required
def workout_session(request, pk):
    """
    Tela principal de execução do treino diário.
    Apresenta lista de exercícios com faixas de carga recomendadas e checkboxes.
    """
    workout = get_object_or_404(
        ScheduledWorkout.objects.select_related('annual_plan', 'phase', 'template'),
        pk=pk,
        annual_plan__user=request.user
    )
    records = workout.exercise_records.select_related('exercise__primary_muscle').order_by('order')

    context = {
        'workout': workout,
        'records': records,
        'today': timezone.localdate(),
    }
    return render(request, 'progress/workout_session.html', context)


@login_required
def toggle_exercise_checkbox(request, record_id):
    """
    Ponto central de interação do usuário: altera o status do checkbox de um exercício.
    Registra data/hora, recalcula progresso da sessão e da semana.
    Retorna o fragmento HTML renderizado via HTMX sem recarregar a tela.
    """
    record = get_object_or_404(
        WorkoutExerciseRecord.objects.select_related('scheduled_workout__annual_plan'),
        pk=record_id,
        scheduled_workout__annual_plan__user=request.user
    )

    # Inverte o estado do checkbox
    record.is_completed = not record.is_completed
    if record.is_completed:
        record.completed_at = timezone.now()
    else:
        record.completed_at = None
    record.save(update_fields=['is_completed', 'completed_at'])

    # Atualiza o status da sessão e os indicadores semanais de forma atômica
    ProgressService.update_session_and_weekly_progress(record.scheduled_workout)

    workout = record.scheduled_workout

    # Se for uma requisição HTMX, responde apenas com o componente parcial atualizado
    if request.headers.get('HX-Request') or getattr(request, 'htmx', False):
        context = {
            'record': record,
            'workout': workout,
        }
        return render(request, 'progress/components/exercise_row.html', context)

    # Fallback para requisições convencionais
    return redirect('progress:workout_session', pk=workout.pk)


@login_required
def weekly_view(request):
    """
    Painel de acompanhamento semanal e gerenciamento de pendências.
    Apresenta treinos previstos, concluídos, pendentes e reorganização inteligente.
    """
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    if not plan:
        plan = PlanningService.initialize_annual_plan_for_user(request.user)

    target_date_str = request.GET.get('date')
    if target_date_str:
        try:
            ref_date = date.fromisoformat(target_date_str)
        except ValueError:
            ref_date = timezone.localdate()
    else:
        ref_date = timezone.localdate()

    week_data = ProgressService.get_week_summary(plan, ref_date)

    context = {
        'plan': plan,
        'week_data': week_data,
        'ref_date': ref_date,
    }
    return render(request, 'progress/weekly_view.html', context)


@login_required
def calendar_view(request):
    """
    Calendário anual interativo mês a mês.
    Identifica dias de treino (seg/qua/sex) com status real de cumprimento.
    """
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    if not plan:
        plan = PlanningService.initialize_annual_plan_for_user(request.user)

    year = int(request.GET.get('year', timezone.localdate().year))
    month = int(request.GET.get('month', timezone.localdate().month))

    calendar_data = ProgressService.get_month_calendar_data(plan, year, month)

    context = {
        'plan': plan,
        'calendar_data': calendar_data,
        'current_year': year,
        'current_month': month,
    }
    return render(request, 'progress/calendar_view.html', context)

