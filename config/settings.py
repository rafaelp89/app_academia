import os
from pathlib import Path
import environ

# Configura diretório temporário para Matplotlib sem poluir ou falhar em ambiente protegido
os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib')

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Inicialização do django-environ para gerenciar variáveis de ambiente
env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, 'django-insecure-chave-secreta-treinamento-hipertrofia-2026-xyz-dev'),
    ALLOWED_HOSTS=(list, ['127.0.0.1', 'localhost', '*']),
)

# Carrega arquivo .env se existir
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Definição de Aplicações Instaladas
INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Bibliotecas de Terceiros
    'django_htmx',

    # Apps do Projeto (modularizados sob apps/)
    'apps.accounts',
    'apps.training',
    'apps.planning',
    'apps.progress',
    'apps.dashboard',
    'apps.exports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middleware do django-htmx para facilitar a inspeção de requisições HTMX nas views
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Configuração do Banco de Dados (SQLite com persistência real)
# Projetado com Django ORM para permitir migração transparente para PostgreSQL se desejado
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'database' / 'db.sqlite3',
    }
}

# Validações de Senhas do Django
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalização e Fuso Horário Local consistente
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos Estáticos e de Mídia
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações de Redirecionamento de Autenticação
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'accounts:login'
