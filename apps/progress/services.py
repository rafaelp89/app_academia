import calendar
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from .models import ScheduledWorkout, WorkoutExerciseRecord, WeeklyProgress
from apps.planning.models import AnnualPlan

class ProgressService:
    """
    Serviço central de controle de frequência, conclusão por checkboxes
    e acompanhamento do progresso semanal e do calendário.
    """

    @classmethod
    def update_session_and_weekly_progress(cls, workout):
        """
        Atualiza o status da sessão (Concluído vs Pendente) e recalcula
        os indicadores da semana correspondente.
        """
        total = workout.exercise_records.count()
        completed = workout.exercise_records.filter(is_completed=True).count()

        if total > 0 and completed == total:
            workout.status = 'CONCLUIDO'
            if not workout.completed_at:
                workout.completed_at = timezone.now()
        else:
            workout.status = 'PENDENTE'
            workout.completed_at = None

        workout.save(update_fields=['status', 'completed_at'])

        # Atualiza o registro consolidado de WeeklyProgress
        w_date = workout.scheduled_date
        monday = w_date - timedelta(days=w_date.weekday())
        sunday = monday + timedelta(days=6)
        year, week_num, _ = monday.isocalendar()

        week_workouts = ScheduledWorkout.objects.filter(
            annual_plan=workout.annual_plan,
            scheduled_date__gte=monday,
            scheduled_date__lte=sunday
        )

        planned_sessions = week_workouts.count()
        completed_sessions = week_workouts.filter(status='CONCLUIDO').count()

        total_exs = 0
        comp_exs = 0
        for w in week_workouts:
            total_exs += w.total_exercises
            comp_exs += w.completed_exercises

        rate = Decimal((comp_exs / total_exs * 100) if total_exs > 0 else 0).quantize(Decimal('0.1'))

        if completed_sessions == planned_sessions and planned_sessions > 0:
            status = 'CONCLUIDA_TOTAL'
        elif completed_sessions > 0 or comp_exs > 0:
            status = 'CONCLUIDA_PARCIAL'
        elif monday > timezone.localdate():
            status = 'FUTURA'
        else:
            status = 'EM_ANDAMENTO'

        WeeklyProgress.objects.update_or_create(
            annual_plan=workout.annual_plan,
            year=year,
            week_number=week_num,
            defaults={
                'user': workout.annual_plan.user,
                'start_date': monday,
                'end_date': sunday,
                'planned_sessions_count': planned_sessions,
                'completed_sessions_count': completed_sessions,
                'planned_exercises_count': total_exs,
                'completed_exercises_count': comp_exs,
                'completion_rate': rate,
                'status': status,
            }
        )

    @classmethod
    def get_week_summary(cls, plan, ref_date):
        """
        Retorna o panorama detalhado de uma semana de treino:
        sessões planejadas, concluídas, pendentes e percentual.
        """
        monday = ref_date - timedelta(days=ref_date.weekday())
        sunday = monday + timedelta(days=6)
        prev_week = monday - timedelta(days=7)
        next_week = monday + timedelta(days=7)

        workouts = list(ScheduledWorkout.objects.filter(
            annual_plan=plan,
            scheduled_date__gte=monday,
            scheduled_date__lte=sunday
        ).select_related('template', 'phase').prefetch_related('exercise_records__exercise__primary_muscle').order_by('scheduled_date'))

        total_sessions = len(workouts)
        completed_sessions = sum(1 for w in workouts if w.status == 'CONCLUIDO')
        pending_sessions = sum(1 for w in workouts if w.status == 'PENDENTE')
        missed_sessions = sum(1 for w in workouts if w.status == 'NAO_REALIZADO')

        total_exercises = sum(w.total_exercises for w in workouts)
        completed_exercises = sum(w.completed_exercises for w in workouts)
        missing_exercises = total_exercises - completed_exercises

        progress_rate = int((completed_exercises / total_exercises * 100)) if total_exercises > 0 else 0

        # Lista de grupos musculares previstos na semana
        muscle_names = set()
        for w in workouts:
            for rec in w.exercise_records.all():
                muscle_names.add(rec.exercise.primary_muscle.name)

        return {
            'monday': monday,
            'sunday': sunday,
            'prev_week_date': prev_week,
            'next_week_date': next_week,
            'workouts': workouts,
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'pending_sessions': pending_sessions,
            'missed_sessions': missed_sessions,
            'total_exercises': total_exercises,
            'completed_exercises': completed_exercises,
            'missing_exercises': missing_exercises,
            'progress_rate': progress_rate,
            'planned_muscles': sorted(list(muscle_names)),
        }

    @classmethod
    def get_month_calendar_data(cls, plan, year, month):
        """
        Monta a matriz de semanas e dias para o calendário anual,
        associando treinos reais, status e rotas de navegação.
        """
        cal = calendar.Calendar(firstweekday=0) # Segunda-feira como primeiro dia da semana
        month_days = cal.monthdatescalendar(year, month)

        start_month = date(year, month, 1)
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)

        if month == 1:
            prev_month = date(year - 1, 12, 1)
        else:
            prev_month = date(year, month - 1, 1)

        # Busca treinos do intervalo do calendário
        first_date = month_days[0][0]
        last_date = month_days[-1][-1]

        workouts = {
            w.scheduled_date: w
            for w in ScheduledWorkout.objects.filter(
                annual_plan=plan,
                scheduled_date__gte=first_date,
                scheduled_date__lte=last_date
            ).select_related('template', 'phase')
        }

        today = timezone.localdate()
        weeks_data = []

        for week in month_days:
            days_data = []
            for day in week:
                is_curr_month = (day.month == month)
                workout = workouts.get(day)
                is_training_day = day.weekday() in [0, 2, 4] # Seg, Qua, Sex

                days_data.append({
                    'date': day,
                    'day_num': day.day,
                    'is_current_month': is_curr_month,
                    'is_today': (day == today),
                    'is_training_day': is_training_day,
                    'workout': workout,
                })
            weeks_data.append(days_data)

        month_names = [
            '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]

        return {
            'year': year,
            'month': month,
            'month_name': month_names[month],
            'weeks': weeks_data,
            'prev_year': prev_month.year,
            'prev_month': prev_month.month,
            'next_year': next_month.year,
            'next_month': next_month.month,
        }

