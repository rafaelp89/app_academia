from django.db import models

class MuscleGroup(models.Model):
    """Grupo muscular principal da anatomia e cinesiologia."""
    name = models.CharField(max_length=60, unique=True, verbose_name='Grupo Muscular')
    description = models.TextField(blank=True, verbose_name='Descrição Anatômica')

    class Meta:
        verbose_name = 'Grupo Muscular'
        verbose_name_plural = 'Grupos Musculares'
        ordering = ['name']

    def __str__(self):
        return self.name


class Exercise(models.Model):
    """
    Biblioteca de Exercícios.
    Armazena ficha técnica completa com biomecânica, postura, erros comuns e vídeos.
    Para membros inferiores, obedece estritamente ao requisito de máquinas convencionais.
    """
    LOAD_TYPE_CHOICES = [
        ('MAQUINA_PLACAS', 'Máquina com Placas / Seletor de Tijolos'),
        ('MAQUINA_ANILHAS', 'Máquina com Anilhas (Ex: Leg Press 45°)'),
        ('POLIA_CABO', 'Polia com Cabo de Aço'),
        ('HALTER_PAR', 'Halteres (Carga indicada por halter individual)'),
        ('BARRA_GUIADA', 'Barra Guiada / Smith Machine'),
        ('PESO_CORPORAL', 'Peso Corporal / Suspenso'),
    ]

    name = models.CharField(max_length=120, unique=True, verbose_name='Nome do Exercício')
    primary_muscle = models.ForeignKey(
        MuscleGroup,
        on_delete=models.PROTECT,
        related_name='primary_exercises',
        verbose_name='Grupo Muscular Principal'
    )
    secondary_muscles = models.ManyToManyField(
        MuscleGroup,
        blank=True,
        related_name='secondary_exercises',
        verbose_name='Grupos Musculares Secundários'
    )
    equipment = models.CharField(max_length=120, verbose_name='Equipamento Convencional')
    is_lower_body_machine = models.BooleanField(
        default=False,
        verbose_name='É máquina convencional para membros inferiores'
    )
    load_unit_type = models.CharField(
        max_length=30,
        choices=LOAD_TYPE_CHOICES,
        default='MAQUINA_PLACAS',
        verbose_name='Tipo de Resistência / Carga'
    )
    execution_guide = models.TextField(verbose_name='Instruções de Execução')
    posture_tips = models.TextField(verbose_name='Postura e Posicionamento')
    technical_cautions = models.TextField(verbose_name='Cuidados Técnicos e Segurança')
    common_errors = models.TextField(verbose_name='Erros Comuns a Evitar')
    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='Link de Vídeo Curto Demonstrativo (Shorts/Reels)'
    )

    @property
    def youtube_id(self):
        """Extrai o ID do vídeo do YouTube suportando formatos shorts/, watch?v= ou youtu.be/."""
        if not self.video_url:
            return None
        import re
        match = re.search(r'(?:shorts\/|v=|youtu\.be\/)([a-zA-Z0-9_-]{11})', self.video_url)
        if match:
            return match.group(1)
        return None

    @property
    def embed_video_url(self):
        """Retorna a URL de incorporação para player vertical 9:16 estilo TikTok / Shorts."""
        yt_id = self.youtube_id
        if yt_id:
            return f"https://www.youtube.com/embed/{yt_id}?rel=0&modestbranding=1"
        return self.video_url

    @property
    def shorts_url(self):
        """Retorna o link direto no formato YouTube Shorts."""
        yt_id = self.youtube_id
        if yt_id:
            return f"https://www.youtube.com/shorts/{yt_id}"
        return self.video_url

    class Meta:
        verbose_name = 'Exercício'
        verbose_name_plural = 'Exercícios'
        ordering = ['primary_muscle', 'name']

    def __str__(self):
        return f"{self.name} ({self.primary_muscle.name})"


class WorkoutTemplate(models.Model):
    """
    Estrutura padrão de treino (Treino A, B ou C).
    Define o tema da sessão e o dia de referência da semana.
    """
    CODE_CHOICES = [
        ('A', 'Treino A'),
        ('B', 'Treino B'),
        ('C', 'Treino C'),
    ]
    code = models.CharField(max_length=1, choices=CODE_CHOICES, unique=True, verbose_name='Código da Sessão')
    name = models.CharField(max_length=100, verbose_name='Título da Sessão')
    day_of_week_label = models.CharField(max_length=20, verbose_name='Dia da Semana')
    day_of_week_num = models.IntegerField(verbose_name='Dia da Semana (0=Seg, 2=Qua, 4=Sex)')
    focus_summary = models.CharField(max_length=200, verbose_name='Foco Muscular Principal')
    description = models.TextField(verbose_name='Justificativa Técnica e Estratégia')

    class Meta:
        verbose_name = 'Modelo de Sessão (Template)'
        verbose_name_plural = 'Modelos de Sessão (Templates)'
        ordering = ['code']

    def __str__(self):
        return f"Treino {self.code} — {self.day_of_week_label}: {self.name}"


class WorkoutTemplateExercise(models.Model):
    """
    Associação de exercícios ao modelo de treino com prescrição estimada padrão.
    """
    template = models.ForeignKey(
        WorkoutTemplate,
        on_delete=models.CASCADE,
        related_name='template_exercises',
        verbose_name='Sessão'
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='in_templates',
        verbose_name='Exercício'
    )
    order = models.PositiveIntegerField(default=1, verbose_name='Ordem de Execução')
    default_sets = models.PositiveIntegerField(default=3, verbose_name='Séries Padrão')
    reps_min = models.PositiveIntegerField(default=10, verbose_name='Repetições Mínimas')
    reps_max = models.PositiveIntegerField(default=12, verbose_name='Repetições Máximas')
    default_load_min_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=20.0,
        verbose_name='Carga Mínima Estimada (kg)'
    )
    default_load_max_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=35.0,
        verbose_name='Carga Máxima Estimada (kg)'
    )
    default_rest_seconds = models.PositiveIntegerField(default=75, verbose_name='Descanso Sugerido (s)')
    notes = models.CharField(max_length=200, blank=True, verbose_name='Observação Técnica')

    class Meta:
        verbose_name = 'Exercício do Modelo'
        verbose_name_plural = 'Exercícios dos Modelos'
        ordering = ['template', 'order']
        unique_together = ['template', 'exercise']

    def __str__(self):
        return f"{self.template.code} - {self.order}. {self.exercise.name} ({self.default_sets}x{self.reps_min}-{self.reps_max})"

