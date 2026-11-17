from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Exercise, MuscleGroup, WorkoutTemplate

@login_required
def exercise_list(request):
    """Biblioteca de exercícios com filtros por grupo muscular e tipo."""
    muscle_filter = request.GET.get('muscle')
    exercises = Exercise.objects.select_related('primary_muscle').prefetch_related('secondary_muscles').all()

    if muscle_filter:
        exercises = exercises.filter(primary_muscle__name__iexact=muscle_filter)

    muscle_groups = MuscleGroup.objects.all()

    context = {
        'exercises': exercises,
        'muscle_groups': muscle_groups,
        'current_filter': muscle_filter,
    }
    return render(request, 'training/exercise_list.html', context)


@login_required
def exercise_detail(request, pk):
    """Ficha biomecânica completa do exercício."""
    exercise = get_object_or_404(
        Exercise.objects.select_related('primary_muscle').prefetch_related('secondary_muscles'),
        pk=pk
    )
    return render(request, 'training/exercise_detail.html', {'exercise': exercise})


@login_required
def template_list(request):
    """Visualização dos modelos de sessões (Treinos A, B e C)."""
    templates = WorkoutTemplate.objects.prefetch_related('template_exercises__exercise__primary_muscle').all()
    return render(request, 'training/template_list.html', {'templates': templates})

