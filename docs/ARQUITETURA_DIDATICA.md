# 📘 Guia Didático de Arquitetura: Python, Django e Desenvolvimento Full Stack

Este documento foi elaborado para acompanhar seus estudos de programação em **Python** e desenvolvimento web com **Django**, explicando a anatomia de cada componente do seu aplicativo de musculação.

---

## 1. Por que dividir o projeto em Apps Django?

No ecossistema Django, um **projeto** representa o site completo (configurações gerais, banco de dados, middlewares), enquanto cada **app** representa uma unidade funcional modular e coesa de negócio.

A divisão adotada segue o princípio da **Responsabilidade Única (SRP)**:

1. **`accounts`**: Gerencia autenticação nativa do Django (`auth.User`), perfis físicos (`UserProfile`) e metas individuais.
2. **`training`**: Focado no conhecimento cinesiológico — grupos musculares (`MuscleGroup`), ficha biomecânica dos exercícios (`Exercise`) e modelos de sessão A, B e C (`WorkoutTemplate`).
3. **`planning`**: É o cérebro da periodização anual de 12 meses (`AnnualPlan`), das 5 fases de treinamento (`PeriodizationPhase`) e das tomadas de decisão autônomas registradas em `PlanAdjustmentLog`.
4. **`progress`**: Administra a linha do tempo do praticante — sessões agendadas nas segundas, quartas e sextas (`ScheduledWorkout`), registros diários dos exercícios com checkboxes (`WorkoutExerciseRecord`) e consolidação semanal (`WeeklyProgress`).
5. **`dashboard`**: Responsável pela camada analítica, cálculo de KPIs e geração de gráficos vetoriais SVG no servidor via Matplotlib.
6. **`exports`**: Cuida da persistência externa — relatórios CSV com UTF-8 BOM para Excel e serialização/restauração completa em JSON.

---

## 2. Models e o Django ORM (Object-Relational Mapping)

### O que é o ORM?
O ORM permite que você interaja com o banco de dados escrevendo código **Python puro** em vez de comandos SQL manuais (`SELECT`, `INSERT`, `UPDATE`, `DELETE`).

### Como os Models se relacionam?
Existem 3 tipos clássicos de relacionamentos no Django:

1. **`OneToOneField` (Um para Um):**
   - Exemplo: `UserProfile` se relaciona com `User`.
   - *Conceito:* Cada conta de usuário possui exatamente um perfil biométrico associado e vice-versa.

2. **`ForeignKey` (Muitos para Um):**
   - Exemplo: `ScheduledWorkout` pertence a um `AnnualPlan`, e `WorkoutExerciseRecord` pertence a um `ScheduledWorkout`.
   - *Conceito:* Um planejamento anual possui dezenas de sessões agendadas, mas cada sessão agendada pertence estritamente a um único planejamento.
   - Parâmetro `on_delete=models.CASCADE`: Se o planejamento for deletado, suas sessões associadas são removidas automaticamente em cascata para evitar dados órfãos.

3. **`ManyToManyField` (Muitos para Muitos):**
   - Exemplo: `Exercise` se relaciona com `MuscleGroup` em `secondary_muscles`.
   - *Conceito:* O exercício Supino Máquina trabalha primariamente Peitoral, mas ativa secundariamente Tríceps e Deltóides. Da mesma forma, Tríceps é ativado em múltiplos exercícios.

---

## 3. Como funcionam as Migrations?

Migrations são como um **sistema de controle de versão (Git) para a estrutura do seu banco de dados**.

1. Ao alterar ou criar uma classe em `models.py`, você executa:
   ```bash
   python manage.py makemigrations
   ```
   O Django inspeciona o código Python e gera um arquivo de migração (ex: `0001_initial.py`), que traduz as mudanças para uma representação declarativa.
2. Ao executar:
   ```bash
   python manage.py migrate
   ```
   O Django lê essa migração e executa no SQLite (ou PostgreSQL) o comando SQL real correspondente (`CREATE TABLE`, `ALTER TABLE`, etc.), mantendo a tabela interna `django_migrations` para saber quais passos já foram aplicados.

---

## 4. O Ciclo de Vida de uma Requisição: URLs, Views e Templates

Quando você clica em um link ou botão no navegador:

```
Navegador (Cliente) 
       │  (1) Envia requisição HTTP (GET / POST)
       ▼
   config/urls.py  ──►  apps/progress/urls.py
       │  (2) Encontra o padrão de rota e direciona
       ▼
   apps/progress/views.py (Função Python)
       │  (3) Executa a regra de negócio via Service
       │  (4) Consulta dados no banco via Django ORM
       ▼
   templates/progress/workout_session.html
       │  (5) O Template Engine interpola as variáveis Python {{ }} e tags {% %}
       ▼
   HTML Renderizado  ──►  Retornado ao Navegador (Resposta 200 OK)
```

---

## 5. Como o HTMX Atualiza os Checkboxes Instantaneamente

O requisito central do seu projeto é que a única ação diária seja marcar ou desmarcar o checkbox de um exercício, salvando de imediato sem botão extra e sem recarregar a tela inteira.

### Passo a Passo da Comunicação:
1. **No arquivo `exercise_row.html`:**
   ```html
   <button hx-post="/progress/toggle/42/"
           hx-target="#exercise-card-42"
           hx-swap="outerHTML">
       ☑ Concluído
   </button>
   ```
2. **O HTMX intercepta o clique:** Não ocorre o recarregamento total da página. Uma chamada `fetch` assíncrona é enviada em background com cabeçalho `HX-Request: true`.
3. **No arquivo `views.py` (`toggle_exercise_checkbox`):**
   ```python
   record = WorkoutExerciseRecord.objects.get(id=42)
   record.is_completed = not record.is_completed
   record.completed_at = timezone.now() if record.is_completed else None
   record.save()
   ProgressService.update_session_and_weekly_progress(record.scheduled_workout)
   ```
4. **Resposta Parcial com Out-Of-Band (OOB):**
   A view renderiza apenas o trecho HTML do card e adiciona:
   ```html
   <div id="workout-progress-header" hx-swap-oob="true">
       ... nova barra de progresso recalculada ...
   </div>
   ```
5. **O HTMX substitui no DOM:**
   - O card do exercício `#exercise-card-42` é substituído com o estilo verde e timestamp gravado.
   - O cabeçalho `#workout-progress-header` no topo da página é atualizado simultaneamente via `hx-swap-oob`.
   - Zero código JavaScript personalizado foi escrito. Todo o estado reside com segurança no banco SQLite gerenciado pelo Python.

---

## 6. Geração de Gráficos no Servidor com Matplotlib

Muitos projetos dependem de bibliotecas JavaScript volumosas (como Chart.js ou D3.js) que aumentam a complexidade no frontend. 

No seu aplicativo, adotamos a abordagem do **Server-Side Chart Generation**:
1. O Python lê do banco a lista de sessões de cada mês e as taxas de cumprimento semanal.
2. Utilizamos o backend `Agg` do Matplotlib (`matplotlib.use('Agg')`), que opera de forma totalmente headless em servidores Linux (sem precisar de monitor gráfico).
3. O gráfico é desenhado com tema escuro e exportado diretamente para um buffer de memória em formato vetorial **SVG** (`plt.savefig(buffer, format='svg')`).
4. A view Django retorna esse buffer como um `HttpResponse(svg_content, content_type='image/svg+xml')`.
5. No HTML, usamos uma tag padrão `<img src="/dashboard/charts/frequency.svg">`. O navegador mobile desenha o vetor com nitidez cirúrgica e carregamento instantâneo.

---

## 7. Exportação CSV e JSON

### Exportação CSV com UTF-8 BOM (`\ufeff`)
No Brasil, o Excel frequentemente apresenta caracteres corrompidos (como "Treinamento" virando "Treinamento" com símbolos estranhos) caso o arquivo CSV não possua o caractere especial **BOM (Byte Order Mark)**.
No serviço `ExportService.generate_csv_report`:
```python
output.write('\ufeff') # Garante abertura imediata e correta no Excel brasileiro
writer = csv.writer(output, delimiter=';')
```
Isso garante compatibilidade nativa com Excel, Calc e Google Sheets.

### Backup e Restauração em JSON
O `ExportService.generate_json_backup` cria um mapa estruturado do macrociclo, enquanto `restore_from_json` executa a reconstrução das tabelas dentro de uma **transação atômica** (`@transaction.atomic`). Se o arquivo for corrompido ou o schema for inválido durante o upload, o banco desfaz todas as alterações (Rollback), impedindo que dados parciais corrompam o sistema.

---

## 8. Testes Automatizados com Pytest-Django

Testes automatizados asseguram que as regras de negócio não sejam quebradas ao evoluir o código:
- `@pytest.mark.django_db`: Indica ao pytest que aquele teste precisa de acesso ao banco de dados isolado de teste.
- O teste cria um usuário efêmero, inicializa o plano de 12 meses, testa o clique nos checkboxes e verifica com `assert` se o valor no banco mudou conforme esperado.
- Se alguém modificar uma regra (por exemplo, adicionar acidentalmente um agachamento livre no Treino B), o teste `test_lower_body_exercises_strictly_conventional_machines` falhará imediatamente, alertando o desenvolvedor antes de ir para produção.

