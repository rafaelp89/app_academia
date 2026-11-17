from django.db import models
from django.contrib.auth.models import User

class AnnualPlan(models.Model):
    """
    Planejamento Anual de 12 Meses.
    Calcula datas reais de início e término e administra as 52 semanas de treinamento.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='annual_plans',
        verbose_name='Usuário'
    )
    title = models.CharField(
        max_length=150,
        default='Planejamento Anual de Hipertrofia e Recomposição Corporal',
        verbose_name='Título do Planejamento'
    )
    start_date = models.DateField(verbose_name='Data Real de Início')
    end_date = models.DateField(verbose_name='Data de Término (12 Meses)')
    total_weeks = models.PositiveIntegerField(default=52, verbose_name='Total de Semanas')
    is_active = models.BooleanField(default=True, verbose_name='Plano Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Planejamento Anual'
        verbose_name_plural = 'Planejamentos Anuais'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.start_date.strftime('%d/%m/%Y')} a {self.end_date.strftime('%d/%m/%Y')})"


class PeriodizationPhase(models.Model):
    """
    Fase da Periodização Anual.
    Organiza blocos técnicos de treino com metas de hipertrofia, volume e recuperação.
    """
    annual_plan = models.ForeignKey(
        AnnualPlan,
        on_delete=models.CASCADE,
        related_name='phases',
        verbose_name='Planejamento Anual'
    )
    phase_number = models.PositiveIntegerField(verbose_name='Número da Fase')
    name = models.CharField(max_length=150, verbose_name='Nome da Fase')
    objective = models.TextField(verbose_name='Objetivo da Fase')
    start_date = models.DateField(verbose_name='Início da Fase')
    end_date = models.DateField(verbose_name='Término da Fase')
    strategy = models.TextField(verbose_name='Estratégia de Treinamento')
    prioritized_muscles = models.CharField(max_length=200, verbose_name='Grupos Musculares Priorizados')
    weekly_frequency = models.PositiveIntegerField(default=3, verbose_name='Frequência Semanal (Sessões)')
    planned_volume = models.CharField(max_length=150, verbose_name='Volume Semanal Planejado')
    sets_reps_prescription = models.CharField(max_length=150, verbose_name='Séries e Repetições Prescritas')
    rest_interval_seconds = models.PositiveIntegerField(default=75, verbose_name='Intervalo de Descanso Médio (s)')
    intensity_guidance = models.CharField(
        max_length=200,
        verbose_name='Intensidade / Esforço Recomendado (RIR / RPE Educativo)'
    )
    progression_criteria = models.TextField(verbose_name='Critérios Técnicos para Avançar à Próxima Fase')
    is_current = models.BooleanField(default=False, verbose_name='Fase Ativa Atual')
    is_completed = models.BooleanField(default=False, verbose_name='Fase Concluída')

    class Meta:
        verbose_name = 'Fase de Periodização'
        verbose_name_plural = 'Fases de Periodização'
        ordering = ['annual_plan', 'phase_number']
        unique_together = ['annual_plan', 'phase_number']

    def __str__(self):
        return f"Fase {self.phase_number}: {self.name}"


class PlanAdjustmentLog(models.Model):
    """
    Registro Histórico de Decisões e Alterações do Planejamento.
    Garante rastreabilidade transparente de cada decisão autônoma do sistema.
    """
    ACTION_CHOICES = [
        ('FASE_AVANCO', 'Avanço Automático de Fase'),
        ('REORGANIZACAO', 'Reorganização Inteligente de Sessões Pendentes'),
        ('RECUPERACAO', 'Semana de Recuperação / Deload Programada'),
        ('AJUSTE_VOLUME', 'Ajuste Conservador de Prescrição'),
        ('INICIALIZACAO', 'Geração Inicial do Planejamento Anual de 12 Meses'),
    ]

    annual_plan = models.ForeignKey(
        AnnualPlan,
        on_delete=models.CASCADE,
        related_name='adjustment_logs',
        verbose_name='Planejamento Anual'
    )
    date = models.DateField(verbose_name='Data do Evento')
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES, verbose_name='Tipo de Ação')
    reason = models.CharField(max_length=200, verbose_name='Motivo da Ação')
    explanation = models.TextField(verbose_name='Justificativa Técnica e Pedagógica')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Registrado em')

    class Meta:
        verbose_name = 'Histórico de Ajuste do Plano'
        verbose_name_plural = 'Histórico de Ajustes do Plano'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.date.strftime('%d/%m/%Y')}] {self.get_action_type_display()} - {self.reason}"

