import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from apps.planning.models import AnnualPlan
from apps.planning.services import PlanningService
from .services import ExportService

@login_required
def exports_hub(request):
    """Central de exportação de relatórios e backup/restauração do banco de dados."""
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    return render(request, 'exports/hub.html', {'plan': plan})


@login_required
def export_csv(request):
    """Gera e faz download de relatório CSV com UTF-8 BOM compatível diretamente com Excel."""
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    if not plan:
        messages.error(request, "Nenhum planejamento ativo para exportação.")
        return redirect('exports:hub')

    csv_data = ExportService.generate_csv_report(plan)
    response = HttpResponse(csv_data, content_type='text/csv; charset=utf-8-sig')
    filename = f"historico_treinos_{plan.user.username}_{plan.start_date.strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def export_json(request):
    """Gera e faz download do backup integral estruturado em formato JSON."""
    plan = AnnualPlan.objects.filter(user=request.user, is_active=True).first()
    if not plan:
        messages.error(request, "Nenhum planejamento ativo para exportação.")
        return redirect('exports:hub')

    json_data = ExportService.generate_json_backup(plan)
    response = HttpResponse(json_data, content_type='application/json; charset=utf-8')
    filename = f"backup_planejamento_{plan.user.username}_{plan.start_date.strftime('%Y%m%d')}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def restore_json(request):
    """Restaura o planejamento e histórico a partir de um arquivo JSON validado."""
    if request.method == 'POST':
        json_file = request.FILES.get('backup_file')
        if not json_file:
            messages.error(request, "Nenhum arquivo enviado para restauração.")
            return redirect('exports:hub')

        try:
            content = json_file.read().decode('utf-8')
            success, message = ExportService.restore_from_json(request.user, content)
            if success:
                messages.success(request, f"Sucesso: {message}")
            else:
                messages.error(request, f"Falha na validação: {message}")
        except Exception as e:
            messages.error(request, f"Erro ao processar arquivo: {str(e)}")

        return redirect('exports:hub')

    return redirect('exports:hub')

