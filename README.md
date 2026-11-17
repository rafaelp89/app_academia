# 🏋️ Aplicativo Full Stack de Musculação, Hipertrofia & Acompanhamento Anual (12 Meses)

Sistema web Full Stack desenvolvido em **Python 3** e **Django 5**, com interface mobile-first (**HTML5/CSS3**), interações reativas sem JavaScript personalizado via **HTMX**, gráficos analíticos gerados no servidor via **Matplotlib (SVG)** e persistência real em **SQLite/Django ORM**.

---

## 🎯 1. Perfil do Praticante & Diretrizes Físicas
- **Sexo & Idade:** Masculino, 38 anos
- **Estatura & Peso:** 1,75 m | 85,0 kg
- **Biotipo:** Mesomorfo
- **Experiência:** Nível intermediário (conhece a execução dos exercícios básicos)
- **Momento Atual:** Retornando aos treinos após aproximadamente 1 ano de inatividade
- **Objetivo Principal:** Hipertrofia e ganho de massa muscular
- **Objetivo Secundário:** Melhora da composição corporal e definição muscular
- **Frequência Semanal:** 3 dias por semana (Segunda-feira, Quarta-feira e Sexta-feira)
- **Ambiente:** Academia de bairro com equipamentos mecânicos convencionais
- **Membros Inferiores:** **100% estruturado em máquinas convencionais** (Leg Press 45°, Cadeira Extensora, Mesa Flexora, Cadeira Flexora, Cadeira Adutora, Cadeira Abdutora, Panturrilha na Máquina). Zero agachamentos livres com barra.
- **Vídeos Demonstrativos:** **Formato curto vertical (9:16)** ao estilo **TikTok, Instagram Reels e YouTube Shorts** (30 a 60s), com visualização rápida expansível diretamente na tela do treino.
- **Interação Diária:** **Estritamente Checkboxes**. Não há digitação diária de cargas, repetições, RIR ou observações.

---

## 🧱 2. Arquitetura Modular do Projeto

```
meu_treinamento/ (proj_app_academia/)
│
├── manage.py                   # Utilitário de linha de comando do Django
├── requirements.txt            # Dependências Python do projeto
├── pytest.ini                  # Configurações do framework de testes pytest
│
├── config/                     # Configurações centrais do Django
│   ├── settings.py             # Configurações, middlewares, apps e banco
│   ├── urls.py                 # Roteamento raiz da aplicação
│   ├── wsgi.py                 # Ponto de entrada WSGI para produção
│   └── asgi.py                 # Ponto de entrada ASGI assíncrono
│
├── apps/                       # Módulos desacoplados por responsabilidade
│   ├── accounts/               # Autenticação, perfis e diretrizes físicas
│   ├── training/               # Cinesiologia, biblioteca de exercícios e modelos A/B/C
│   ├── planning/               # Macrociclo anual de 12 meses, 5 fases e serviços de progressão
│   ├── progress/               # Calendário real, checklists reativos (HTMX) e pendências
│   ├── dashboard/              # Agregação de KPIs e renderização de gráficos SVG (Matplotlib)
│   └── exports/                # Exportação CSV (UTF-8 BOM), backup e restauração JSON
│
├── templates/                  # Templates HTML5 semânticos (Mobile-First)
│   ├── base.html               # Shell base com cabeçalho, mensagens e navegação inferior
│   ├── components/             # Componentes reutilizáveis (header, bottom_nav)
│   ├── accounts/               # Login e ficha do perfil
│   ├── training/               # Biblioteca de exercícios e ficha biomecânica detalhada
│   ├── planning/               # Macrociclo anual, fases e histórico de decisões
│   ├── progress/               # Tela de treino diário, calendário e painel semanal
│   ├── dashboard/              # Indicadores visuais e gráficos vetoriais
│   └── exports/                # Central de download CSV/JSON e restauração
│
├── static/                     # Arquivos estáticos
│   ├── css/styles.css          # Design system mobile-first responsivo
│   └── js/htmx.min.js          # Biblioteca HTMX (vendored localmente, sem CDN)
│
├── database/                   # Persistência e backups
│   └── db.sqlite3              # Banco de dados SQLite persistente
│
└── tests/                      # Bateria de testes automatizados (pytest-django)
    ├── test_planning.py        # Validação do plano de 12 meses, datas e máquinas de perna
    ├── test_checklist.py       # Validação da persistência imediata dos checkboxes
    ├── test_backlog_and_progression.py # Reorganização de pendências e avanço de fase
    ├── test_dashboard_and_charts.py    # Indicadores e geração de SVG pelo Matplotlib
    └── test_exports.py         # CSV com UTF-8 BOM e ciclo completo de backup/restore JSON
```

---

## 🚀 3. Guia de Instalação e Execução

### Pré-requisitos
- Python 3.12 ou superior instalado

### Passo 1 — Clonar e Acessar o Diretório
```bash
cd "Área de trabalho/proj_app_academia"
```

### Passo 2 — Ativar o Ambiente Virtual
O ambiente virtual já está criado na pasta `venv`. Para ativá-lo:
```bash
source venv/bin/activate
```

### Passo 3 — Executar as Migrações do Banco de Dados
```bash
python manage.py migrate
```

### Passo 4 — Inicializar os Dados do Planejamento Anual
O comando customizado `init_training_plan` cria o usuário padrão com seu perfil físico e gera automaticamente os 12 meses de treinos reais:
```bash
python manage.py init_training_plan
```

### Passo 5 — Iniciar o Servidor de Desenvolvimento
```bash
python manage.py runserver
```
Acesse no seu navegador: **http://127.0.0.1:8000**

### 🔑 Credenciais de Acesso Padrão
- **Usuário:** `rafael`
- **Senha:** `academia123`

---

## 🧪 4. Execução dos Testes Automatizados

O projeto conta com uma suíte de 12 testes cobrindo todas as regras de negócio:
```bash
pytest
```
*Todos os 12 testes são executados com validação de banco em memória ou SQLite de teste, garantindo 100% de conformidade.*

---

## 🎓 5. Fundamentação Técnica e Aprendizado em Python / Django

### Como funciona a interação diária sem JavaScript?
O usuário abre o treino e clica no checkbox. O **HTMX** intercepta o clique do botão e dispara um `POST` para a rota `/progress/toggle/<id>/`. A view Django processa a requisição em Python:
1. Inverte o booleano `is_completed`.
2. Registra o timestamp atual em `completed_at` (ou `None` se desmarcado).
3. Recalcula o status da sessão e o resumo semanal.
4. Renderiza apenas o template parcial `exercise_row.html` e a barra de progresso via swap Out-of-Band (`hx-swap-oob`).
5. O DOM é atualizado de forma instantânea sem recarregar a página e sem uma única linha de JavaScript escrita no cliente!

### Gráficos no Servidor com Matplotlib
Em vez de carregar bibliotecas JS pesadas (Chart.js ou ApexCharts), os gráficos de frequência mensal e cumprimento semanal são gerados diretamente no Python utilizando `matplotlib.pyplot` com backend `Agg` (headless). A view retorna o SVG bruto com cabeçalho `image/svg+xml`, permitindo renderização nítida em qualquer resolução com peso mínimo na rede.

