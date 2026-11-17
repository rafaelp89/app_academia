from django.db import models
from django.contrib.auth.models import User
from apps.planning.models import AnnualPlan, PeriodizationPhase
from apps.training.models import Exercise, WorkoutTemplate

class ScheduledWorkout(models.Model):
    """
    Sessão agendada no calendário anual de 12 meses.
    Vinculada a datas reais (segundas, quartas e sextas-feiras).
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONCLUIDO', 'Concluído'),
        ('NAO_REALIZADO', 'Não Realizado'),
        ('REORGANIZADO', 'Reorganizado'),
    ]

    annual_plan = models.ForeignKey(
        AnnualPlan,
        on_delete=models.CASCADE,
        related_name='scheduled_workouts',
        verbose_name='Planejamento Anual'
    )
    phase = models.ForeignKey(
        PeriodizationPhase,
        on_delete=models.PROTECT,
        related_name='phase_workouts',
        verbose_name='Fase de Periodização'
    )
    template = models.ForeignKey(
        WorkoutTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='scheduled_instances',
        verbose_name='Modelo Base'
    )
    scheduled_date = models.DateField(verbose_name='Data Programada (Real)')
    session_code = models.CharField(max_length=2, verbose_name='Código (A, B, C)')
    title = models.CharField(max_length=120, verbose_name='Título da Sessão')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE', verbose_name='Status')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Concluído em')
    reorganization_note = models.CharField(max_length=255, blank=True, verbose_name='Nota de Reorganização')

    class Meta:
        verbose_name = 'Sessão Agendada'
        verbose_name_plural = 'Sessões Agendadas'
        ordering = ['scheduled_date', 'session_code']
        unique_together = ['annual_plan', 'scheduled_date']

    def __str__(self):
        return f"{self.scheduled_date.strftime('%d/%m/%Y')} — Treino {self.session_code}: {self.title} [{self.get_status_display()}]"

    @property
    def total_exercises(self):
        return self.exercise_records.count()

    @property
    def completed_exercises(self):
        return self.exercise_records.filter(is_completed=True).count()

    @property
    def completion_percentage(self):
        total = self.total_exercises
        if total == 0:
            return 0
        return int((self.completed_exercises / total) * 100)


class WorkoutExerciseRecord(models.Model):
    """
    Registro individual de exercício por sessão.
    A única ação diária do usuário é marcar/desmarcar o campo is_completed (checkbox).
    Não armazena nem exige preenchimento de cargas reais levantadas ou repetições feitas.
    """
    scheduled_workout = models.ForeignKey(
        ScheduledWorkout,
        on_delete=models.CASCADE,
        related_name='exercise_records',
        verbose_name='Sessão Agendada'
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.PROTECT,
        related_name='recorded_instances',
        verbose_name='Exercício'
    )
    order = models.PositiveIntegerField(default=1, verbose_name='Ordem')
    prescribed_sets = models.PositiveIntegerField(default=3, verbose_name='Séries Prescritas')
    prescribed_reps = models.CharField(max_length=30, default='10–12', verbose_name='Repetições Prescritas')
    load_min_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name='Carga Mínima Estimada (kg)'
    )
    load_max_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name='Carga Máxima Estimada (kg)'
    )
    rest_seconds = models.PositiveIntegerField(default=75, verbose_name='Descanso Sugerido (s)')
    is_completed = models.BooleanField(default=False, verbose_name='Exercício Concluído (Checkbox)')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Horário da Conclusão')

    class Meta:
        verbose_name = 'Registro de Exercício'
        verbose_name_plural = 'Registros de Exercícios'
        ordering = ['scheduled_workout', 'order']

    def __str__(self):
        status = "✔ Concluído" if self.is_completed else "☐ Pendente"
        return f"{self.scheduled_workout.session_code} - {self.exercise.name} [{status}]"


class WeeklyProgress(models.Model):
    """
    Consolidação semanal de cumprimento e regularidade.
    Permite visualizar facilmente treinos planejados, concluídos e pendências.
    """
    STATUS_CHOICES = [
        ('FUTURA', 'Semana Futura'),
        ('EM_ANDAMENTO', 'Semana em Andamento'),
        ('CONCLUIDA_TOTAL', '100% Concluída'),
        ('CONCLUIDA_PARCIAL', 'Parcialmente Concluída'),
        ('NAO_REALIZADA', 'Sem Treinos Realizados'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='weekly_progresses',
        verbose_name='Usuário'
    )
    annual_plan = models.ForeignKey(
        AnnualPlan,
        on_delete=models.CASCADE,
        related_name='weekly_summaries',
        verbose_name='Planejamento Anual'
    )
    year = models.PositiveIntegerField(verbose_name='Ano')
    week_number = models.PositiveIntegerField(verbose_name='Número da Semana (1 a 52)')
    start_date = models.DateField(verbose_name='Início da Semana (Segunda-feira)')
    end_date = models.DateField(verbose_name='Fim da Semana (Domingo)')
    planned_sessions_count = models.PositiveIntegerField(default=3, verbose_name='Sessões Planejadas')
    completed_sessions_count = models.PositiveIntegerField(default=0, verbose_name='Sessões Concluídas')
    planned_exercises_count = models.PositiveIntegerField(default=0, verbose_name='Exercícios Planejados')
    completed_exercises_count = models.PositiveIntegerField(default=0, verbose_name='Exercícios Concluídos')
    completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        verbose_name='Taxa de Conclusão (%)'
    )
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default='EM_ANDAMENTO',
        verbose_name='Status Semanal'
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Progresso Semanal'
        verbose_name_plural = 'Progressos Semanais'
        ordering = ['year', 'week_number']
        unique_together = ['annual_plan', 'year', 'week_number']

    def __str__(self):
        return f"Semana {self.week_number}/{self.year}: {self.completed_sessions_count}/{self.planned_sessions_count} treinos ({self.completion_rate}%)"

