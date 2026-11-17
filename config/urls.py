from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def root_redirect(request):
    """Redireciona a raiz para o dashboard principal ou tela de login."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('accounts:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect, name='root_redirect'),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('training/', include('apps.training.urls', namespace='training')),
    path('planning/', include('apps.planning.urls', namespace='planning')),
    path('progress/', include('apps.progress.urls', namespace='progress')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('exports/', include('apps.exports.urls', namespace='exports')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

