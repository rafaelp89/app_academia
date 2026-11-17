import pytest
import json
from django.contrib.auth.models import User
from apps.planning.services import PlanningService
from apps.exports.services import ExportService
from apps.planning.models import AnnualPlan

@pytest.mark.django_db
class TestExportsAndRestore:
    def test_csv_export_with_utf8_bom(self):
        user = User.objects.create_user(username='aluno_csv', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        csv_bytes = ExportService.generate_csv_report(plan)
        assert csv_bytes.startswith(b'\xef\xbb\xbf') # UTF-8 BOM bytes

        text = csv_bytes.decode('utf-8-sig')
        assert "Data Programada;Dia da Semana;Sessão" in text
        assert "Leg Press 45°" in text
        assert "Supino Máquina Sentado" in text

    def test_json_backup_and_restore_roundtrip(self):
        user = User.objects.create_user(username='aluno_backup', password='password123')
        plan = PlanningService.initialize_annual_plan_for_user(user)

        # Marca um exercício para conferir persistência no restore
        first_rec = plan.scheduled_workouts.first().exercise_records.first()
        first_rec.is_completed = True
        first_rec.save()

        # Gera JSON
        backup_json = ExportService.generate_json_backup(plan)
        assert len(backup_json) > 1000

        data = json.loads(backup_json)
        assert data['annual_plan']['total_weeks'] == 52
        assert len(data['phases']) == 5
        assert len(data['scheduled_workouts']) > 150

        # Restaura em outro usuário (ou no mesmo)
        user2 = User.objects.create_user(username='aluno_restaurado', password='password123')
        success, msg = ExportService.restore_from_json(user2, backup_json)
        assert success is True

        new_plan = AnnualPlan.objects.get(user=user2, is_active=True)
        assert new_plan.phases.count() == 5
        assert new_plan.scheduled_workouts.count() == plan.scheduled_workouts.count()
        restored_rec = new_plan.scheduled_workouts.first().exercise_records.first()
        assert restored_rec.is_completed is True

