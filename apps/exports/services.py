import io
import csv
import json
from decimal import Decimal
from datetime import date, datetime
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import UserProfile
from apps.planning.models import AnnualPlan, PeriodizationPhase, PlanAdjustmentLog
from apps.training.models import Exercise, MuscleGroup, WorkoutTemplate
from apps.progress.models import ScheduledWorkout, WorkoutExerciseRecord, WeeklyProgress

class ExportService:
    """
    Serviço de Exportação e Restauração de Dados.
    Garante exportação CSV com UTF-8 BOM para Excel e backup completo e auditável em JSON.
    """

    @classmethod
    def generate_csv_report(cls, plan):
        """
        Gera relatório CSV com UTF-8 BOM (\ufeff), cabeçalhos em português e
        uma linha por exercício agendado.
        """
        output = io.StringIO()
        # Grava o caractere BOM para que o Excel abra automaticamente no charset correto
        output.write('\ufeff')

        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # Cabeçalhos padronizados em português
        headers = [
            "Data Programada",
            "Dia da Semana",
            "Sessão",
            "Título da Sessão",
            "Fase da Periodização",
            "Status da Sessão",
            "Ordem",
            "Exercício",
            "Grupo Muscular Principal",
            "Equipamento Convencional",
            "Tipo de Carga",
            "Séries Prescritas",
            "Repetições Prescritas",
            "Carga Mínima Sugerida (kg)",
            "Carga Máxima Sugerida (kg)",
            "Descanso Sugerido (s)",
            "Concluído (Checkbox)",
            "Horário da Conclusão",
            "Nota de Reorganização"
        ]
        writer.writerow(headers)

        records = WorkoutExerciseRecord.objects.filter(
            scheduled_workout__annual_plan=plan
        ).select_related(
            'scheduled_workout__phase',
            'scheduled_workout__template',
            'exercise__primary_muscle'
        ).order_by('scheduled_workout__scheduled_date', 'order')

        weekday_names = {
            0: 'Segunda-feira',
            1: 'Terça-feira',
            2: 'Quarta-feira',
            3: 'Quinta-feira',
            4: 'Sexta-feira',
            5: 'Sábado',
            6: 'Domingo',
        }

        for rec in records:
            w = rec.scheduled_workout
            w_date = w.scheduled_date
            weekday_str = weekday_names.get(w_date.weekday(), '')

            writer.writerow([
                w_date.strftime('%d/%m/%Y'),
                weekday_str,
                f"Treino {w.session_code}",
                w.title,
                w.phase.name,
                w.get_status_display(),
                rec.order,
                rec.exercise.name,
                rec.exercise.primary_muscle.name,
                rec.exercise.equipment,
                rec.exercise.get_load_unit_type_display(),
                rec.prescribed_sets,
                rec.prescribed_reps,
                str(rec.load_min_kg).replace('.', ','),
                str(rec.load_max_kg).replace('.', ','),
                rec.rest_seconds,
                "SIM" if rec.is_completed else "NÃO",
                rec.completed_at.strftime('%d/%m/%Y %H:%M:%S') if rec.completed_at else "—",
                w.reorganization_note or "—"
            ])

        return output.getvalue().encode('utf-8-sig')

    @classmethod
    def generate_json_backup(cls, plan):
        """
        Serializa todos os dados do planejamento, fases, treinos, checklists e perfil
        em formato JSON legível e estruturado.
        """
        user = plan.user
        profile = getattr(user, 'profile', None)

        backup_dict = {
            'metadata': {
                'version': '1.0',
                'exported_at': timezone.now().isoformat(),
                'export_type': 'FULL_BACKUP',
            },
            'user_profile': {
                'username': user.username,
                'email': user.email,
                'age': profile.age if profile else 38,
                'height_m': float(profile.height_m) if profile else 1.75,
                'current_weight_kg': float(profile.current_weight_kg) if profile else 85.0,
                'biotype': profile.biotype if profile else 'Mesomorfo',
                'experience_level': profile.experience_level if profile else 'Intermediário',
                'gym_type': profile.gym_type if profile else 'Academia convencional de bairro',
                'main_goal': profile.main_goal if profile else 'Hipertrofia e ganho de massa muscular',
                'secondary_goal': profile.secondary_goal if profile else 'Melhorar composição corporal',
                'supplementation': profile.supplementation if profile else 'Creatina diariamente',
                'hydration': profile.hydration if profile else 'Consumo regular e abundante de água',
                'diet_guidance': profile.diet_guidance if profile else 'Alimentação regular',
            },
            'annual_plan': {
                'title': plan.title,
                'start_date': plan.start_date.isoformat(),
                'end_date': plan.end_date.isoformat(),
                'total_weeks': plan.total_weeks,
                'is_active': plan.is_active,
            },
            'phases': [],
            'adjustment_logs': [],
            'scheduled_workouts': [],
        }

        # Fases
        for ph in plan.phases.all().order_by('phase_number'):
            backup_dict['phases'].append({
                'phase_number': ph.phase_number,
                'name': ph.name,
                'objective': ph.objective,
                'start_date': ph.start_date.isoformat(),
                'end_date': ph.end_date.isoformat(),
                'strategy': ph.strategy,
                'prioritized_muscles': ph.prioritized_muscles,
                'weekly_frequency': ph.weekly_frequency,
                'planned_volume': ph.planned_volume,
                'sets_reps_prescription': ph.sets_reps_prescription,
                'rest_interval_seconds': ph.rest_interval_seconds,
                'intensity_guidance': ph.intensity_guidance,
                'progression_criteria': ph.progression_criteria,
                'is_current': ph.is_current,
                'is_completed': ph.is_completed,
            })

        # Logs de ajuste
        for log in plan.adjustment_logs.all().order_by('created_at'):
            backup_dict['adjustment_logs'].append({
                'date': log.date.isoformat(),
                'action_type': log.action_type,
                'reason': log.reason,
                'explanation': log.explanation,
                'created_at': log.created_at.isoformat(),
            })

        # Sessões e Exercícios
        for w in plan.scheduled_workouts.all().order_by('scheduled_date'):
            workout_entry = {
                'scheduled_date': w.scheduled_date.isoformat(),
                'session_code': w.session_code,
                'title': w.title,
                'status': w.status,
                'completed_at': w.completed_at.isoformat() if w.completed_at else None,
                'reorganization_note': w.reorganization_note,
                'phase_number': w.phase.phase_number,
                'exercises': [],
            }
            for rec in w.exercise_records.all().order_by('order'):
                workout_entry['exercises'].append({
                    'exercise_name': rec.exercise.name,
                    'order': rec.order,
                    'prescribed_sets': rec.prescribed_sets,
                    'prescribed_reps': rec.prescribed_reps,
                    'load_min_kg': float(rec.load_min_kg),
                    'load_max_kg': float(rec.load_max_kg),
                    'rest_seconds': rec.rest_seconds,
                    'is_completed': rec.is_completed,
                    'completed_at': rec.completed_at.isoformat() if rec.completed_at else None,
                })
            backup_dict['scheduled_workouts'].append(workout_entry)

        return json.dumps(backup_dict, ensure_ascii=False, indent=2)

    @classmethod
    @transaction.atomic
    def restore_from_json(cls, user, json_str):
        """
        Valida e restaura o planejamento e histórico a partir do JSON de backup.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return False, f"JSON corrompido ou formato inválido: {str(e)}"

        if 'annual_plan' not in data or 'phases' not in data or 'scheduled_workouts' not in data:
            return False, "Estrutura do arquivo de backup incompleta. Chaves obrigatórias ausentes."

        # Desativa planos atuais
        AnnualPlan.objects.filter(user=user, is_active=True).update(is_active=False)

        plan_data = data['annual_plan']
        plan = AnnualPlan.objects.create(
            user=user,
            title=plan_data.get('title', 'Planejamento Restaurado'),
            start_date=date.fromisoformat(plan_data['start_date']),
            end_date=date.fromisoformat(plan_data['end_date']),
            total_weeks=plan_data.get('total_weeks', 52),
            is_active=True,
        )

        # Fases
        phase_map = {}
        for p in data['phases']:
            ph_obj = PeriodizationPhase.objects.create(
                annual_plan=plan,
                phase_number=p['phase_number'],
                name=p['name'],
                objective=p['objective'],
                start_date=date.fromisoformat(p['start_date']),
                end_date=date.fromisoformat(p['end_date']),
                strategy=p.get('strategy', ''),
                prioritized_muscles=p.get('prioritized_muscles', ''),
                weekly_frequency=p.get('weekly_frequency', 3),
                planned_volume=p.get('planned_volume', ''),
                sets_reps_prescription=p.get('sets_reps_prescription', ''),
                rest_interval_seconds=p.get('rest_interval_seconds', 75),
                intensity_guidance=p.get('intensity_guidance', ''),
                progression_criteria=p.get('progression_criteria', ''),
                is_current=p.get('is_current', False),
                is_completed=p.get('is_completed', False),
            )
            phase_map[p['phase_number']] = ph_obj

        # Logs
        for log in data.get('adjustment_logs', []):
            PlanAdjustmentLog.objects.create(
                annual_plan=plan,
                date=date.fromisoformat(log['date']),
                action_type=log['action_type'],
                reason=log['reason'],
                explanation=log['explanation'],
            )

        # Treinos e Exercícios
        exercise_cache = {e.name: e for e in Exercise.objects.all()}
        template_cache = {t.code: t for t in WorkoutTemplate.objects.all()}

        for w_data in data['scheduled_workouts']:
            ph = phase_map.get(w_data.get('phase_number')) or plan.phases.first()
            tmpl = template_cache.get(w_data['session_code'])

            scheduled = ScheduledWorkout.objects.create(
                annual_plan=plan,
                phase=ph,
                template=tmpl,
                scheduled_date=date.fromisoformat(w_data['scheduled_date']),
                session_code=w_data['session_code'],
                title=w_data.get('title', f"Treino {w_data['session_code']}"),
                status=w_data.get('status', 'PENDENTE'),
                completed_at=datetime.fromisoformat(w_data['completed_at']) if w_data.get('completed_at') else None,
                reorganization_note=w_data.get('reorganization_note', ''),
            )

            for ex_data in w_data.get('exercises', []):
                ex_name = ex_data['exercise_name']
                ex_obj = exercise_cache.get(ex_name)
                if not ex_obj:
                    # Cria exercício com fallback se não existia no banco
                    default_muscle = MuscleGroup.objects.first()
                    ex_obj = Exercise.objects.create(
                        name=ex_name,
                        primary_muscle=default_muscle,
                        equipment='Equipamento Convencional',
                        execution_guide='Instruções restauradas do backup.',
                        posture_tips='Postura firme.',
                        technical_cautions='Cuidado geral.',
                        common_errors='Evitar trancos.',
                    )
                    exercise_cache[ex_name] = ex_obj

                WorkoutExerciseRecord.objects.create(
                    scheduled_workout=scheduled,
                    exercise=ex_obj,
                    order=ex_data.get('order', 1),
                    prescribed_sets=ex_data.get('prescribed_sets', 3),
                    prescribed_reps=ex_data.get('prescribed_reps', '10–12'),
                    load_min_kg=Decimal(str(ex_data.get('load_min_kg', 20.0))),
                    load_max_kg=Decimal(str(ex_data.get('load_max_kg', 35.0))),
                    rest_seconds=ex_data.get('rest_seconds', 75),
                    is_completed=ex_data.get('is_completed', False),
                    completed_at=datetime.fromisoformat(ex_data['completed_at']) if ex_data.get('completed_at') else None,
                )

        return True, "Planejamento e histórico restaurados com sucesso!"

