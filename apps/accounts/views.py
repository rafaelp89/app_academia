from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile

def login_view(request):
    """View de login do praticante."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bem-vindo de volta, {user.first_name or user.username}!")
            return redirect('dashboard:index')
        else:
            messages.error(request, "Credenciais inválidas. Verifique seu usuário e senha.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """View de encerramento de sessão."""
    logout(request)
    messages.info(request, "Sessão encerrada com segurança.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Visualização e conferência das diretrizes do perfil físico."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})

