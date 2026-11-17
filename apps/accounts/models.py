from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """
    Perfil do praticante de musculação.
    Armazena características corporais e objetivos para fundamentar as
    diretrizes pedagógicas e a periodização do treinamento anual.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuário'
    )
    age = models.PositiveIntegerField(default=38, verbose_name='Idade (anos)')
    height_m = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.75,
        verbose_name='Altura (m)'
    )
    current_weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=85.0,
        verbose_name='Peso Atual Informado (kg)'
    )
    biotype = models.CharField(
        max_length=50,
        default='Mesomorfo',
        verbose_name='Biotipo Autodeclarado'
    )
    experience_level = models.CharField(
        max_length=100,
        default='Intermediário - Retornando após 1 ano parado',
        verbose_name='Nível de Experiência'
    )
    training_frequency_per_week = models.PositiveIntegerField(
        default=3,
        verbose_name='Frequência Semanal (dias)'
    )
    gym_type = models.CharField(
        max_length=150,
        default='Academia simples de bairro com equipamentos convencionais',
        verbose_name='Tipo de Academia'
    )
    main_goal = models.CharField(
        max_length=150,
        default='Hipertrofia e ganho de massa muscular',
        verbose_name='Objetivo Principal'
    )
    secondary_goal = models.CharField(
        max_length=150,
        default='Melhorar a composição corporal e definição muscular',
        verbose_name='Objetivo Complementar'
    )
    supplementation = models.CharField(
        max_length=150,
        default='Creatina diariamente',
        verbose_name='Suplementação Atual'
    )
    hydration = models.CharField(
        max_length=150,
        default='Consumo regular e abundante de água',
        verbose_name='Hidratação'
    )
    diet_guidance = models.CharField(
        max_length=200,
        default='Alimentação regular, controle consciente do consumo de açúcar',
        verbose_name='Alimentação'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Cadastro')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')

    class Meta:
        verbose_name = 'Perfil do Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f"Perfil de {self.user.username} ({self.age} anos, {self.current_weight_kg}kg)"

