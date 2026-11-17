from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.planning.services import PlanningService
from apps.planning.models import AnnualPlan

class Command(BaseCommand):
    help = 'Inicializa os dados mestres, usuário padrão e planejamento anual de 12 meses.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='rafael', help='Nome de usuário do praticante')
        parser.add_argument('--password', type=str, default='academia123', help='Senha de acesso')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': 'Rafael',
                'email': 'rafael@treinamento.local',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Usuário '{username}' criado com sucesso."))
        else:
            self.stdout.write(f"Usuário '{username}' já existente.")

        # Atualiza o perfil com as características reais fornecidas
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.age = 38
        profile.height_m = 1.75
        profile.current_weight_kg = 85.0
        profile.biotype = 'Mesomorfo'
        profile.experience_level = 'Intermediário (Retornando após 1 ano parado)'
        profile.training_frequency_per_week = 3
        profile.gym_type = 'Academia simples de bairro com equipamentos convencionais'
        profile.main_goal = 'Hipertrofia e ganho de massa muscular'
        profile.secondary_goal = 'Melhora da composição corporal e definição muscular'
        profile.supplementation = 'Creatina diariamente'
        profile.hydration = 'Consumo regular e abundante de água'
        profile.diet_guidance = 'Regular, controle consciente do consumo de açúcar'
        profile.save()

        self.stdout.write("Inicializando exercícios, modelos e planejamento anual...")
        plan = PlanningService.initialize_annual_plan_for_user(user)

        total_sessions = plan.scheduled_workouts.count()
        total_phases = plan.phases.count()

        self.stdout.write(self.style.SUCCESS(
            f"Planejamento anual gerado com sucesso!\n"
            f"Período: {plan.start_date.strftime('%d/%m/%Y')} a {plan.end_date.strftime('%d/%m/%Y')}\n"
            f"Fases criadas: {total_phases}\n"
            f"Sessões agendadas (Seg/Qua/Sex): {total_sessions}\n"
            f"Credenciais de acesso:\n"
            f"  Usuário: {username}\n"
            f"  Senha: {password}"
        ))

