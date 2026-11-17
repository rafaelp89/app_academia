from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.training.models import MuscleGroup, Exercise, WorkoutTemplate, WorkoutTemplateExercise
from apps.planning.models import AnnualPlan, PeriodizationPhase, PlanAdjustmentLog
from apps.progress.models import ScheduledWorkout, WorkoutExerciseRecord, WeeklyProgress

class PlanningService:
    """
    Motor de Periodização, Prescrição e Planejamento Anual de 12 Meses.
    Implementa as diretrizes científicas da Educação Física para praticante
    de nível intermediário retornando após 1 ano de inatividade.
    """

    @classmethod
    def seed_initial_data(cls):
        """Popula grupos musculares e biblioteca de exercícios com foco em máquinas convencionais."""
        muscles = {
            'Peitoral': 'Músculos peitoral maior e peitoral menor.',
            'Dorsais (Costas)': 'Latíssimo do dorso, trapézio e rombóides.',
            'Deltóides (Ombros)': 'Porções anterior, lateral e posterior dos ombros.',
            'Bíceps': 'Bíceps braquial e braquiorradial.',
            'Tríceps': 'Tríceps braquial (cabeças medial, lateral e longa).',
            'Quadríceps': 'Reto femoral, vasto lateral, medial e intermédio (coxa anterior).',
            'Isquiotibiais': 'Bíceps femoral, semitendíneo e semimembranoso (coxa posterior).',
            'Glúteos e Abdutores': 'Glúteo máximo, médio, mínimo e tensor da fáscia lata.',
            'Adutores': 'Adutor magno, longo e curto da coxa.',
            'Panturrilhas': 'Gastrocnêmio e sóleo (tríceps sural).',
            'Abdômen': 'Reto abdominal e oblíquos (estabilização do core).',
        }
        muscle_objs = {}
        for name, desc in muscles.items():
            obj, _ = MuscleGroup.objects.get_or_create(name=name, defaults={'description': desc})
            muscle_objs[name] = obj

        exercises_data = [
            # EXERCÍCIOS DE MEMBROS INFERIORES: ESTRITAMENTE MÁQUINAS CONVENCIONAIS
            {
                'name': 'Leg Press 45°',
                'primary_muscle': muscle_objs['Quadríceps'],
                'equipment': 'Máquina Leg Press 45° com anilhas',
                'is_lower_body_machine': True,
                'load_unit_type': 'MAQUINA_ANILHAS',
                'execution_guide': 'Posicione os pés na largura dos ombros no meio da plataforma. Destrave a máquina segurando as manoplas laterais. Desça controlando o peso até formar um ângulo de 90° nos joelhos sem arredondar a lombar. Empurre a plataforma com o calcanhar e o meio do pé, sem travar completamente os joelhos no topo.',
                'posture_tips': 'Mantenha as costas e os glúteos firmemente colados ao encosto durante todo o arco de movimento. Joelhos alinhados com a ponta dos pés.',
                'technical_cautions': 'Nunca deixe a pelve retroverter (descolar do banco) no ponto mais baixo para proteger a coluna lombar.',
                'common_errors': 'Colocar os joelhos para dentro (valgo dinâmico), tirar o quadril do banco e hiperextender os joelhos no final.',
                'video_url': 'https://www.youtube.com/shorts/K0d7ItBGRvM',
            },
            {
                'name': 'Cadeira Extensora',
                'primary_muscle': muscle_objs['Quadríceps'],
                'equipment': 'Cadeira Extensora convencional de placas',
                'is_lower_body_machine': True,
                'load_unit_type': 'MAQUINA_PLACAS',
                'execution_guide': 'Ajuste o encosto de modo que o eixo de rotação da máquina coincida exatamente com a articulação dos joelhos. Apoie o rolo acolchoado logo acima dos tornozelos. Estenda os joelhos até a contração máxima do quadríceps e retorne lentamente na fase excêntrica.',
                'posture_tips': 'Mantenha as mãos firmes nos apoios laterais e o tronco vertical sem inclinar para trás.',
                'technical_cautions': 'Evite trancos no ponto de partida; movimento controlado preserva a cartilagem patelofemoral.',
                'common_errors': 'Descer a carga despencando sem controle excêntrico e elevar o quadril do assento.',
                'video_url': 'https://www.youtube.com/shorts/GcWsKoElyMo',
            },
            {
                'name': 'Mesa Flexora',
                'primary_muscle': muscle_objs['Isquiotibiais'],
                'equipment': 'Mesa Flexora deitada convencional',
                'is_lower_body_machine': True,
                'load_unit_type': 'MAQUINA_PLACAS',
                'execution_guide': 'Deite de bruços com o rolo posicionado logo abaixo da panturrilha (acima do tendão de Aquiles). Alinhe os joelhos com o eixo da máquina. Flexione as pernas aproximando os calcanhares dos glúteos de forma controlada. Retorne estendendo sem deixar os tijolos baterem.',
                'posture_tips': 'Mantenha o quadril e o abdômen pressionados contra o banco durante todo o exercício.',
                'technical_cautions': 'Não arquear a região lombar ao levantar a carga.',
                'common_errors': 'Erguer o quadril da mesa ao flexionar as pernas e fazer impulsos com o tronco.',
                'video_url': 'https://www.youtube.com/shorts/8WUxvSpXbVs',
            },
            {
                'name': 'Cadeira Flexora',
                'primary_muscle': muscle_objs['Isquiotibiais'],
                'equipment': 'Cadeira Flexora sentada convencional',
                'is_lower_body_machine': True,
                'load_unit_type': 'MAQUINA_PLACAS',
                'execution_guide': 'Sente-se com as costas apoiadas. Trave a almofada de suporte sobre as coxas. Posicione o rolo atrás dos tornozelos. Puxe os calcanhares para baixo e para trás contraindo ativamente os isquiotibiais. Controle a volta.',
                'posture_tips': 'Coluna alinhada ao encosto, trave bem o apoio sobre a coxa para manter a estabilidade pélvica.',
                'technical_cautions': 'Excelente alternativa com menor estresse na coluna lombar para quem retorna após período inativo.',
                'common_errors': 'Apoio superior solto, permitindo que as pernas se movimentem fora do eixo anatômico.',
                'video_url': 'https://www.youtube.com/shorts/w8ZEXsKL2M4',
            },
            {
                'name': 'Cadeira Abdutora',
                'primary_muscle': muscle_objs['Glúteos e Abdutores'],
                'equipment': 'Cadeira Abdutora de placas',
                'is_lower_body_machine': True,
                'load_unit_type': 'MAQUINA_PLACAS',
                'execution_guide': 'Sente-se com as costas no encosto e os apoios acolchoados na face externa dos joelhos. Abra as pernas contra a resistência até o máximo de amplitude confortável, segure 1 segundo e feche com controle cadenciado.',
                'posture_tips': 'Mantenha a pelve neutra e o tronco ereto.',
                'technical_cautions': 'Fortalecimento fundamental do glúteo médio para estabilização pélvica e prevenção de dores articulares.',
                'common_errors': 'Usar impulso do tronco ou deixar as pernas fecharem repentinamente.',
                'video_url': 'https://www.youtube.com/shorts/GeRnJv8wmFo',
            },
            {
                'name': 'Cadeira Adutora',
                'primary_muscle': muscle_objs['Adutores'],
                'equipment': 'Cadeira Adutora de placas',
                'is_lower_body_machine': True,
                'load_unit_type': 'MAQUINA_PLACAS',
                'execution_guide': 'Sente-se com os apoios acolchoados na face interna dos joelhos. Aproxime as pernas contra a resistência até quase se tocarem. Mantenha 1 segundo de contração no ponto final e retorne controlando.',
                'posture_tips': 'Tronco encostado, pés relaxados nos apoios correspondentes.',
                'technical_cautions': 'Inicie com amplitude moderada para evitar estiramento dos tendões adutores.',
                'common_errors': 'Movimentos balísticos rápidos e falta de controle na fase de abertura.',
                'video_url': 'https://www.youtube.com/shorts/9Xk3I-Cnp7I',
            },
            {
                'name': 'Panturrilha na Máquina (Gêmeos Sentado / Em Pé)',
                'primary_muscle': muscle_objs['Panturrilhas'],
                'equipment': 'Máquina de panturrilha sentada ou em pé',
                'is_lower_body_machine': True,
                'load_unit_type': 'MAQUINA_PLACAS',
                'execution_guide': 'Apoie a porção anterior dos pés na borda da plataforma, deixando os calcanhares livres. Desça os calcanhares ao máximo sentindo o alongamento do tríceps sural. Eleve os calcanhares o mais alto possível na ponta dos pés, sustentando a contração.',
                'posture_tips': 'Mantenha o corpo alinhado e o movimento estritamente concentrado no tornozelo.',
                'technical_cautions': 'Faça uma pausa de 1 segundo embaixo para dissipar a energia elástica do tendão calcâneo.',
                'common_errors': 'Fazer repetições curtas e quicadas sem amplitude real de dorsiflexão e flexão plantar.',
                'video_url': 'https://www.youtube.com/shorts/GwW-7MuMBaw',
            },

            # EXERCÍCIOS DE MEMBROS SUPERIORES E TRONCO CONVENCIONAIS
            {
                'name': 'Supino Máquina Sentado',
                'primary_muscle': muscle_objs['Peitoral'],
                'equipment': 'Máquina articulada ou convergente de supino',
                'is_lower_body_machine': False,
                'load_unit_type': 'MAQUINA_PLACAS',
                'execution_guide': 'Ajuste a altura do banco para que as manoplas fiquem na linha média do peitoral. Retraia as escápulas contra o encosto. Empurre as manoplas estendendo os cotovelos sem travar a articulação e retorne com controle até o alongamento do peito.',
                'posture_tips': 'Pés firmes no chão, escápulas aduzidas e deprimidas.',
                'technical_cautions': 'Excelente segurança para retorno aos treinos, eliminando risco de queda de barra.',
                'common_errors': 'Projetar os ombros para frente no final do movimento e deixar os cotovelos excessivamente abertos.',
                'video_url': 'https://www.youtube.com/shorts/tTp0LgDVcQ4',
            },
            {
                'name': 'Puxada Frontal na Polia',
                'primary_muscle': muscle_objs['Dorsais (Costas)'],
                'equipment': 'Polia alta com barra pulley aberta',
                'is_lower_body_machine': False,
                'load_unit_type': 'POLIA_CABO',
                'execution_guide': 'Segure a barra com pegada pronada ligeiramente mais larga que os ombros. Sente-se e trave as coxas sob o rolo. Com o peito aberto e leve inclinação do tronco, puxe a barra em direção à parte superior do peito puxando com os cotovelos.',
                'posture_tips': 'Mantenha o peito estufado e inicie o movimento pela depressão das escápulas.',
                'technical_cautions': 'Nunca puxe a barra por trás da nuca para evitar estresse lesivo no manguito rotador.',
                'common_errors': 'Balançar o tronco excessivamente para trás usando inércia lombar.',
                'video_url': 'https://www.youtube.com/shorts/Guvf4EHqYE0',
            },
            {
                'name': 'Desenvolvimento Máquina para Ombros',
                'primary_muscle': muscle_objs['Deltóides (Ombros)'],
                'equipment': 'Máquina de desenvolvimento sentado',
                'is_lower_body_machine': False,
                'load_unit_type': 'MAQUINA_PLACAS',
                'execution_guide': 'Ajuste o banco para que as manoplas comecem na altura das orelhas/ombros. Empurre verticalmente até a extensão dos braços sem hiperestender cotovelos. Desça controlando até a altura do queixo.',
                'posture_tips': 'Costas totalmente apoiadas no encosto, abdômen contraído.',
                'technical_cautions': 'Cotovelos ligeiramente à frente do plano coronal (plano escapular).',
                'common_errors': 'Arredondar a lombar descolando o quadril para transformar o exercício em supino inclinado.',
                'video_url': 'https://www.youtube.com/shorts/OPrRH47EBmQ',
            },
            {
                'name': 'Remada Baixa na Polia (Triângulo)',
                'primary_muscle': muscle_objs['Dorsais (Costas)'],
                'equipment': 'Polia baixa com puxador triângulo',
                'is_lower_body_machine': False,
                'load_unit_type': 'POLIA_CABO',
                'execution_guide': 'Sente-se com os pés apoiados na plataforma e joelhos semi-flexionados. Segure o triângulo, mantenha o tronco ereto e puxe o acessório em direção ao abdômen, espremendo as escápulas atrás.',
                'posture_tips': 'Coluna reta, peito erguido, não curve as costas para frente.',
                'technical_cautions': 'Concentre-se em puxar com os cotovelos rentes ao corpo.',
                'common_errors': 'Jogar o tronco para frente e para trás feito remo de barco.',
                'video_url': 'https://www.youtube.com/shorts/ZdWFKfJ9TmE',
            },
            {
                'name': 'Tríceps na Polia (Barra Reta / Corda)',
                'primary_muscle': muscle_objs['Tríceps'],
                'equipment': 'Polia alta com barra reta ou corda',
                'is_lower_body_machine': False,
                'load_unit_type': 'POLIA_CABO',
                'execution_guide': 'Posicione-se em frente à polia com tronco levemente inclinado. Mantenha os cotovelos fixos ao lado das costelas. Empurre o cabo para baixo estendendo totalmente os cotovelos. Retorne até formar 90 graus.',
                'posture_tips': 'Ombros baixos e estáveis; apenas os antebraços se movem.',
                'technical_cautions': 'Evite afastar os cotovelos do tronco durante a execução.',
                'common_errors': 'Mover os cotovelos para frente e para trás, transformando o exercício em pulldown.',
                'video_url': 'https://www.youtube.com/shorts/0C6tpFgUKC4',
            },
            {
                'name': 'Rosca Bíceps na Polia Baixa',
                'primary_muscle': muscle_objs['Bíceps'],
                'equipment': 'Polia baixa com barra reta ou curvada',
                'is_lower_body_machine': False,
                'load_unit_type': 'POLIA_CABO',
                'execution_guide': 'Segure a barra com pegada supinada. Mantenha os cotovelos colados ao tronco e flexione os antebraços levando a barra em direção aos ombros. Controle a descida resistindo à tensão constante do cabo.',
                'posture_tips': 'Coluna ereta, joelhos destravados, pés firmes.',
                'technical_cautions': 'Tensão contínua proporcionada pela polia é ideal para ganho de massa com baixo estresse articular.',
                'common_errors': 'Usar impulsos com o tronco e levantar os cotovelos para frente.',
                'video_url': 'https://www.youtube.com/shorts/zqklqTcOsbo',
            },
            {
                'name': 'Elevação Lateral com Halteres',
                'primary_muscle': muscle_objs['Deltóides (Ombros)'],
                'equipment': 'Par de halteres convencionais',
                'is_lower_body_machine': False,
                'load_unit_type': 'HALTER_PAR',
                'execution_guide': 'Em pé com halteres ao lado do corpo e cotovelos discretamente semi-flexionados. Eleve os braços lateralmente até a altura dos ombros no plano escapular. Desça com controle sem deixar os halteres tocarem as coxas.',
                'posture_tips': 'Mantenha o pescoço relaxado e escápulas estáveis.',
                'technical_cautions': 'Priorize a técnica e a cadência sobre cargas pesadas para isolar o deltóide lateral.',
                'common_errors': 'Encolher os ombros ativando trapézio superior ou dar trancos com as pernas.',
                'video_url': 'https://www.youtube.com/shorts/tlb_oTahYdw',
            },
            {
                'name': 'Crucifixo Máquina (Peck Deck / Voador)',
                'primary_muscle': muscle_objs['Peitoral'],
                'equipment': 'Máquina Voador / Peck Deck convencional',
                'is_lower_body_machine': False,
                'load_unit_type': 'MAQUINA_PLACAS',
                'execution_guide': 'Ajuste a altura do banco para que as manoplas ou almofadas fiquem alinhadas à altura média do tórax. Feche os braços à frente contraindo o peitoral, pause 1 segundo e abra controlando até o limite seguro de mobilidade.',
                'posture_tips': 'Mantenha as escápulas coladas ao encosto e o peito estufado.',
                'technical_cautions': 'Não hiperestenda os ombros para trás além da linha do tronco para preservar a cápsula articular.',
                'common_errors': 'Perder o contato das costas com o banco ou dobrar excessivamente os cotovelos.',
                'video_url': 'https://www.youtube.com/shorts/HOC7eFHGdes',
            },
            {
                'name': 'Abdominal na Máquina / Crunch Controlado',
                'primary_muscle': muscle_objs['Abdômen'],
                'equipment': 'Máquina de abdominal ou banco declinado',
                'is_lower_body_machine': False,
                'load_unit_type': 'MAQUINA_PLACAS',
                'execution_guide': 'Apoie o peito ou segure as alças da máquina. Enrole o tronco flexionando a coluna torácica e contraindo o abdômen ao expirar. Retorne inspirando devagar sem perder a tensão abdominal.',
                'posture_tips': 'Concentre a força no reto abdominal em vez de puxar com os flexores do quadril.',
                'technical_cautions': 'Movimento curto e focado na flexão da coluna toracolombar.',
                'common_errors': 'Puxar o pescoço ou fletir apenas o quadril mantendo a coluna rígida.',
                'video_url': 'https://www.youtube.com/shorts/yhdwnvYBbDM',
            },
        ]

        exercise_map = {}
        for item in exercises_data:
            ex_obj, _ = Exercise.objects.update_or_create(
                name=item['name'],
                defaults={
                    'primary_muscle': item['primary_muscle'],
                    'equipment': item['equipment'],
                    'is_lower_body_machine': item['is_lower_body_machine'],
                    'load_unit_type': item['load_unit_type'],
                    'execution_guide': item['execution_guide'],
                    'posture_tips': item['posture_tips'],
                    'technical_cautions': item['technical_cautions'],
                    'common_errors': item['common_errors'],
                    'video_url': item['video_url'],
                }
            )
            exercise_map[item['name']] = ex_obj

        # MODELOS DE SESSÃO: TREINOS A, B e C
        # Justificativa Técnica:
        # Frequência de 3 dias/semana (Segunda, Quarta e Sexta).
        # Treino A: Superiores (Empurrar e Puxar) + Estabilidade. Permite estímulo equilibrado no tronco.
        # Treino B: Membros Inferiores 100% em Máquinas Convencionais. 48h de descanso para os superiores.
        # Treino C: Tronco & Membros (Corpo Inteiro / Estímulo Complementar), garantindo frequência 2x semanal
        # para os grandes grupos musculares sem sobrecarga de volume diário.
        templates_data = [
            {
                'code': 'A',
                'name': 'Superiores & Tronco (Força e Estabilidade)',
                'day_of_week_label': 'Segunda-feira',
                'day_of_week_num': 0,
                'focus_summary': 'Peito, Costas, Ombros, Tríceps e Abdômen',
                'description': 'Sessão de abertura semanal focada nos grandes grupos do tronco. Permite ativação neuromuscular precisa com máquinas e polias, garantindo estabilidade e baixo risco de lesão.',
                'exercises': [
                    ('Supino Máquina Sentado', 1, 3, 10, 12, Decimal('20.0'), Decimal('35.0'), 75, 'Ajuste a pegada na linha dos mamilos.'),
                    ('Puxada Frontal na Polia', 2, 3, 10, 12, Decimal('25.0'), Decimal('40.0'), 75, 'Puxe até o topo do esterno.'),
                    ('Desenvolvimento Máquina para Ombros', 3, 3, 10, 12, Decimal('10.0'), Decimal('25.0'), 75, 'Movimento vertical controlado.'),
                    ('Tríceps na Polia (Barra Reta / Corda)', 4, 3, 12, 15, Decimal('15.0'), Decimal('25.0'), 60, 'Foco no tríceps com cotovelos colados.'),
                    ('Rosca Bíceps na Polia Baixa', 5, 3, 10, 12, Decimal('10.0'), Decimal('20.0'), 60, 'Tensão contínua nos bíceps.'),
                    ('Abdominal na Máquina / Crunch Controlado', 6, 3, 15, 20, Decimal('15.0'), Decimal('30.0'), 60, 'Cadência suave de contração.'),
                ]
            },
            {
                'code': 'B',
                'name': 'Membros Inferiores (100% Máquinas Convencionais)',
                'day_of_week_label': 'Quarta-feira',
                'day_of_week_num': 2,
                'focus_summary': 'Quadríceps, Isquiotibiais, Glúteos, Adutores e Panturrilhas',
                'description': 'Treinamento completo de membros inferiores estruturado exclusivamente em equipamentos mecânicos com guias e encostos. Elimina compressão axial excessiva da coluna livre e proporciona hipertrofia segura.',
                'exercises': [
                    ('Leg Press 45°', 1, 3, 10, 12, Decimal('40.0'), Decimal('70.0'), 90, 'Pés firmes, não tirar o quadril do encosto.'),
                    ('Cadeira Extensora', 2, 3, 12, 15, Decimal('20.0'), Decimal('35.0'), 75, 'Pausa de 1s no topo da extensão.'),
                    ('Mesa Flexora', 3, 3, 10, 12, Decimal('15.0'), Decimal('30.0'), 75, 'Controle excêntrico na descida.'),
                    ('Cadeira Abdutora', 4, 3, 12, 15, Decimal('25.0'), Decimal('45.0'), 60, 'Estabilidade de glúteo médio.'),
                    ('Cadeira Adutora', 5, 3, 12, 15, Decimal('25.0'), Decimal('45.0'), 60, 'Trabalho de adutores da coxa.'),
                    ('Panturrilha na Máquina (Gêmeos Sentado / Em Pé)', 6, 4, 15, 20, Decimal('20.0'), Decimal('40.0'), 60, 'Alongamento completo do calcanhar.'),
                ]
            },
            {
                'code': 'C',
                'name': 'Corpo Inteiro & Densidade de Estímulo (Full Body Máquinas)',
                'day_of_week_label': 'Sexta-feira',
                'day_of_week_num': 4,
                'focus_summary': 'Estímulo secundário semanal para equilíbrio simétrico e hipertrofia',
                'description': 'Sessão de fechamento da semana que reforça dorsais, peito, ombros e cadeia posterior com máquinas seguras, completando a meta de volume de 12 a 15 séries por grupo muscular.',
                'exercises': [
                    ('Remada Baixa na Polia (Triângulo)', 1, 3, 10, 12, Decimal('25.0'), Decimal('45.0'), 75, 'Costas retas e contração escapular.'),
                    ('Crucifixo Máquina (Peck Deck / Voador)', 2, 3, 10, 12, Decimal('20.0'), Decimal('35.0'), 75, 'Isolamento do peitoral sem risco.'),
                    ('Elevação Lateral com Halteres', 3, 3, 12, 15, Decimal('5.0'), Decimal('10.0'), 60, 'Carga por halter. Priorize a forma.'),
                    ('Cadeira Flexora', 4, 3, 10, 12, Decimal('20.0'), Decimal('35.0'), 75, 'Posteriores em posição sentada.'),
                    ('Cadeira Extensora', 5, 3, 12, 15, Decimal('20.0'), Decimal('35.0'), 60, 'Estímulo de volume final no quadríceps.'),
                    ('Abdominal na Máquina / Crunch Controlado', 6, 3, 15, 20, Decimal('15.0'), Decimal('30.0'), 60, 'Fortalecimento do core.'),
                ]
            },
        ]

        for tmpl_data in templates_data:
            tmpl, _ = WorkoutTemplate.objects.update_or_create(
                code=tmpl_data['code'],
                defaults={
                    'name': tmpl_data['name'],
                    'day_of_week_label': tmpl_data['day_of_week_label'],
                    'day_of_week_num': tmpl_data['day_of_week_num'],
                    'focus_summary': tmpl_data['focus_summary'],
                    'description': tmpl_data['description'],
                }
            )
            for ex_name, order, s, r_min, r_max, l_min, l_max, rest, notes in tmpl_data['exercises']:
                if ex_name in exercise_map:
                    WorkoutTemplateExercise.objects.update_or_create(
                        template=tmpl,
                        exercise=exercise_map[ex_name],
                        defaults={
                            'order': order,
                            'default_sets': s,
                            'reps_min': r_min,
                            'reps_max': r_max,
                            'default_load_min_kg': l_min,
                            'default_load_max_kg': l_max,
                            'default_rest_seconds': rest,
                            'notes': notes,
                        }
                    )

    @classmethod
    @transaction.atomic
    def initialize_annual_plan_for_user(cls, user):
        """
        Gera o planejamento completo de 12 meses a partir da data de criação.
        Cria as 5 fases de periodização e todas as sessões das segundas, quartas e sextas.
        """
        # Garante dados iniciais
        cls.seed_initial_data()

        # Cria ou obtém perfil
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # Desativa planos anteriores se houver
        AnnualPlan.objects.filter(user=user, is_active=True).update(is_active=False)

        start_date = timezone.localdate()
        end_date = start_date + timedelta(days=365)

        plan = AnnualPlan.objects.create(
            user=user,
            title='Planejamento Anual de Hipertrofia e Recomposição Corporal (3x/semana)',
            start_date=start_date,
            end_date=end_date,
            total_weeks=52,
            is_active=True
        )

        # ESTRUTURA DAS 5 FASES DA PERIODIZAÇÃO ANUAL (52 Semanas)
        # 1. Readaptação: Semanas 1 a 6 (~1.5 meses)
        # 2. Hipertrofia Básica & Volume: Semanas 7 a 18 (~3 meses)
        # 3. Força Submáxima & Intensidade: Semanas 19 a 30 (~3 meses)
        # 4. Hipertrofia Avançada & Densidade: Semanas 31 a 42 (~3 meses)
        # 5. Consolidação & Deload Anual: Semanas 43 a 52 (~2.5 meses)
        f1_end = start_date + timedelta(weeks=6) - timedelta(days=1)
        f2_start = f1_end + timedelta(days=1)
        f2_end = f2_start + timedelta(weeks=12) - timedelta(days=1)
        f3_start = f2_end + timedelta(days=1)
        f3_end = f3_start + timedelta(weeks=12) - timedelta(days=1)
        f4_start = f3_end + timedelta(days=1)
        f4_end = f4_start + timedelta(weeks=12) - timedelta(days=1)
        f5_start = f4_end + timedelta(days=1)
        f5_end = end_date

        phases_config = [
            {
                'num': 1,
                'name': 'Fase 1: Readaptação Anatômica e Retorno Progressivo',
                'objective': 'Restauração da eficiência neuromuscular, adaptação tendínea e articular, tolerância ao esforço após 1 ano parado.',
                'start': start_date,
                'end': f1_end,
                'strategy': 'Cargas conservadoras, cadência controlada (2s excêntrica / 1s concêntrica). Foco no aprendizado e precisão motora.',
                'muscles': 'Todos os grupos musculares principais com distribuição harmônica.',
                'freq': 3,
                'volume': '12 a 15 séries totais por sessão (3 séries por exercício).',
                'sets_reps': '3 séries de 12 a 15 repetições.',
                'rest': 60,
                'intensity': 'RPE 6 a 7 (3 a 4 repetições de reserva). Não treinar até a falha muscular concêntrica.',
                'criteria': 'Completar pelo menos 80% das sessões da fase com boa tolerância articular e sem dores crônicas.',
                'is_current': True,
                'load_factor': Decimal('1.00'),  # base das faixas estimadas
            },
            {
                'num': 2,
                'name': 'Fase 2: Hipertrofia Básica e Volume Acumulativo',
                'objective': 'Aumento planejado do volume de treino para estimular a síntese proteica muscular e hipertrofia sarcoplasmática/miofibrilar.',
                'start': f2_start,
                'end': f2_end,
                'strategy': 'Transição para a faixa clássica de hipertrofia. Aumento progressivo e conservador da faixa de trabalho.',
                'muscles': 'Tronco (peitoral e dorsais) e cadeia inferior em máquinas.',
                'freq': 3,
                'volume': '15 a 18 séries totais por sessão (3 a 4 séries por exercício).',
                'sets_reps': '3 a 4 séries de 10 a 12 repetições.',
                'rest': 75,
                'intensity': 'RPE 7 a 8 (2 repetições de reserva). Esforço consistente com execução limpa.',
                'criteria': 'Frequência superior a 80% nas 12 semanas e cumprimento dos exercícios semanais.',
                'is_current': False,
                'load_factor': Decimal('1.10'),  # +10% nas faixas sugeridas de trabalho
            },
            {
                'num': 3,
                'name': 'Fase 3: Hipertrofia com Intensidade e Força Submáxima',
                'objective': 'Desenvolvimento de tensão mecânica através de repetições mais baixas e maior intervalo de descanso entre séries.',
                'start': f3_start,
                'end': f3_end,
                'strategy': 'Foco em exercícios multiarticulares guiados (Leg Press, Supino Máquina, Puxadas). Descanso ampliado.',
                'muscles': 'Ênfase em grupos de grande massa muscular.',
                'freq': 3,
                'volume': '15 séries por sessão com maior densidade de carga.',
                'sets_reps': '3 a 4 séries de 8 a 10 repetições.',
                'rest': 90,
                'intensity': 'RPE 8 (1 a 2 repetições de reserva). Máxima concentração mecânica.',
                'criteria': 'Domínio das faixas com técnica preservada e regularidade mensal comprovada.',
                'is_current': False,
                'load_factor': Decimal('1.20'),  # +20% na faixa sugerida
            },
            {
                'num': 4,
                'name': 'Fase 4: Hipertrofia Avançada e Densidade de Estímulo',
                'objective': 'Otimização da densidade de trabalho, combinação de faixas de repetições e estímulo metabólico final.',
                'start': f4_start,
                'end': f4_end,
                'strategy': 'Combinação de séries pesadas com finalizações metabólicas nas máquinas isoladoras.',
                'muscles': 'Equilíbrio estético, deltóides, dorsais e pernas.',
                'freq': 3,
                'volume': '18 séries por sessão com ritmo contínuo.',
                'sets_reps': '3 a 4 séries de 8 a 12 repetições (ondulação intra-sessão).',
                'rest': 75,
                'intensity': 'RPE 8 a 8.5 (1 a 2 repetições de reserva).',
                'criteria': 'Atingimento das 42 semanas de treinamento acumulado.',
                'is_current': False,
                'load_factor': Decimal('1.25'),
            },
            {
                'num': 5,
                'name': 'Fase 5: Consolidação, Deload Ativo e Reavaliação Anual',
                'objective': 'Consolidação das adaptações de hipertrofia de 12 meses, redução de fadiga residual acumulada e preparação para novo ciclo.',
                'start': f5_start,
                'end': f5_end,
                'strategy': 'Introdução de semanas de deload estratégico (-30% de volume), preservação da técnica e consistência.',
                'muscles': 'Manutenção equilibrada e preservação articular.',
                'freq': 3,
                'volume': '12 séries por sessão com recuperação rápida.',
                'sets_reps': '3 séries de 10 a 12 repetições.',
                'rest': 75,
                'intensity': 'RPE 7 (2 a 3 repetições de reserva). Treino regenerativo e de consolidação.',
                'criteria': 'Conclusão bem-sucedida do macrociclo anual de 52 semanas.',
                'is_current': False,
                'load_factor': Decimal('1.15'),
            },
        ]

        created_phases = []
        for p in phases_config:
            phase_obj = PeriodizationPhase.objects.create(
                annual_plan=plan,
                phase_number=p['num'],
                name=p['name'],
                objective=p['objective'],
                start_date=p['start'],
                end_date=p['end'],
                strategy=p['strategy'],
                prioritized_muscles=p['muscles'],
                weekly_frequency=p['freq'],
                planned_volume=p['volume'],
                sets_reps_prescription=p['sets_reps'],
                rest_interval_seconds=p['rest'],
                intensity_guidance=p['intensity'],
                progression_criteria=p['criteria'],
                is_current=p['is_current'],
                is_completed=False,
            )
            created_phases.append((phase_obj, p['load_factor']))

        # GERAÇÃO DO CALENDÁRIO COMPLETO DE SESSÕES (Segunda=0, Quarta=2, Sexta=4)
        templates = {t.code: t for t in WorkoutTemplate.objects.prefetch_related('template_exercises__exercise').all()}
        code_by_weekday = {0: 'A', 2: 'B', 4: 'C'}

        current_day = start_date
        while current_day <= end_date:
            weekday = current_day.weekday()
            if weekday in code_by_weekday:
                code = code_by_weekday[weekday]
                tmpl = templates.get(code)
                if tmpl:
                    # Identifica em qual fase esta data se encontra
                    matched_phase = None
                    matched_factor = Decimal('1.0')
                    for ph, factor in created_phases:
                        if ph.start_date <= current_day <= ph.end_date:
                            matched_phase = ph
                            matched_factor = factor
                            break
                    if not matched_phase:
                        matched_phase = created_phases[-1][0]
                        matched_factor = created_phases[-1][1]

                    scheduled = ScheduledWorkout.objects.create(
                        annual_plan=plan,
                        phase=matched_phase,
                        template=tmpl,
                        scheduled_date=current_day,
                        session_code=code,
                        title=tmpl.name,
                        status='PENDENTE'
                    )

                    # Cria os registros de exercícios com faixas de carga adaptadas à fase
                    for tmpl_ex in tmpl.template_exercises.all():
                        # Ajuste conservador e proporcional por fase
                        min_load = (tmpl_ex.default_load_min_kg * matched_factor).quantize(Decimal('0.5'))
                        max_load = (tmpl_ex.default_load_max_kg * matched_factor).quantize(Decimal('0.5'))

                        WorkoutExerciseRecord.objects.create(
                            scheduled_workout=scheduled,
                            exercise=tmpl_ex.exercise,
                            order=tmpl_ex.order,
                            prescribed_sets=tmpl_ex.default_sets,
                            prescribed_reps=f"{tmpl_ex.reps_min}–{tmpl_ex.reps_max}",
                            load_min_kg=min_load,
                            load_max_kg=max_load,
                            rest_seconds=tmpl_ex.default_rest_seconds,
                            is_completed=False
                        )

            current_day += timedelta(days=1)

        # Registra o log pedagógico inicial no histórico do plano
        PlanAdjustmentLog.objects.create(
            annual_plan=plan,
            date=start_date,
            action_type='INICIALIZACAO',
            reason='Criação do Macrociclo Anual de 12 Meses',
            explanation=(
                f"Planejamento de 12 meses gerado automaticamente de {start_date.strftime('%d/%m/%Y')} "
                f"a {end_date.strftime('%d/%m/%Y')}. Estruturado em 3 sessões semanais fixas: "
                "Segunda (Treino A - Superiores), Quarta (Treino B - Membros Inferiores em Máquinas Convencionais) "
                "e Sexta (Treino C - Full Body & Densidade). Prescrições de carga calculadas como estimativas "
                "iniciais de trabalho para readaptação progressiva e hipertrofia segura."
            )
        )

        return plan

    @classmethod
    @transaction.atomic
    def reorganize_pending_workouts(cls, plan):
        """
        Gerenciador inteligente de pendências da semana atual.
        Se uma sessão não foi feita em dia anterior, analisa o impacto muscular e decide
        reorganizar a ordem ou manter a prioridade sem empilhar volume de forma perigosa.
        """
        today = timezone.localdate()
        current_monday = today - timedelta(days=today.weekday())
        current_sunday = current_monday + timedelta(days=6)

        week_workouts = ScheduledWorkout.objects.filter(
            annual_plan=plan,
            scheduled_date__gte=current_monday,
            scheduled_date__lte=current_sunday
        ).order_by('scheduled_date')

        missed = [w for w in week_workouts if w.scheduled_date < today and w.status == 'PENDENTE' and w.completed_exercises == 0]
        future_or_today = [w for w in week_workouts if w.scheduled_date >= today]

        if not missed:
            return {
                'success': True,
                'message': 'Nenhuma sessão pendente de dias passados nesta semana para reorganizar.'
            }

        # Analisa a sessão perdida
        first_missed = missed[0]
        explanation = ""

        if first_missed.session_code == 'A' and future_or_today:
            # Segunda perdida. Se hoje for quarta e houver treino B agendado:
            # Não transferimos os 12 exercícios de uma vez.
            # Preserva-se a recuperação ou ajusta-se a ordem.
            first_missed.status = 'NAO_REALIZADO'
            first_missed.reorganization_note = 'Não realizado na data original. Volume não acumulado para preservar recuperação neuromuscular.'
            first_missed.save(update_fields=['status', 'reorganization_note'])

            explanation = (
                f"A sessão de Segunda-feira (Treino A - Superiores) não foi realizada. "
                "Conforme os princípios científicos de treinamento de força, NÃO foi feita a junção dos exercícios "
                "na sessão seguinte para evitar volume agudo excessivo e fadiga articular. A sessão B (Membros Inferiores em Máquinas) "
                "foi preservada com carga e descanso ideais, mantendo o histórico de pendência registrado."
            )
        else:
            for w in missed:
                w.status = 'NAO_REALIZADO'
                w.reorganization_note = 'Sessão pendente arquivada como não realizada para proteger o descanso.'
                w.save(update_fields=['status', 'reorganization_note'])

            explanation = (
                "Sessões pendentes anteriores foram marcadas como não realizadas para evitar acúmulo desmedido "
                "de séries na mesma semana. O histórico foi preservado integralmente."
            )

        PlanAdjustmentLog.objects.create(
            annual_plan=plan,
            date=today,
            action_type='REORGANIZACAO',
            reason='Manejo Inteligente de Sessões Pendentes',
            explanation=explanation
        )

        return {
            'success': True,
            'message': 'Reorganização concluída com sucesso. Recuperação preservada sem acúmulo excessivo.'
        }

    @classmethod
    @transaction.atomic
    def evaluate_and_advance_phase(cls, plan):
        """
        Avalia o avanço para a próxima fase com base no tempo decorrido e na adesão (frequência).
        """
        today = timezone.localdate()
        current_phase = plan.phases.filter(is_current=True).first()

        if not current_phase:
            return {'success': False, 'message': 'Nenhuma fase ativa no momento.'}

        next_phase = plan.phases.filter(phase_number=current_phase.phase_number + 1).first()
        if not next_phase:
            return {'success': False, 'message': 'Você já se encontra na última fase do planejamento anual.'}

        # Estatísticas da fase atual
        phase_workouts = ScheduledWorkout.objects.filter(
            annual_plan=plan,
            phase=current_phase
        )
        total_sessions = phase_workouts.count()
        completed_sessions = phase_workouts.filter(status='CONCLUIDO').count()
        completion_ratio = (completed_sessions / total_sessions) if total_sessions > 0 else 0

        # Regra de avanço técnico:
        # Se a data atual alcançou o término da fase OU se a taxa de cumprimento atingir ao menos 75%
        eligible = (today >= current_phase.end_date) or (completion_ratio >= 0.75 and total_sessions >= 12)

        if not eligible and today < current_phase.end_date:
            return {
                'success': False,
                'message': (
                    f"A fase atual ({current_phase.name}) está programada até {current_phase.end_date.strftime('%d/%m/%Y')}. "
                    f"Conclusão atual: {completed_sessions}/{total_sessions} sessões ({int(completion_ratio*100)}%). "
                    "Recomenda-se manter a estrutura e consolidar o hábito antes de avançar."
                )
            }

        # Efetua o avanço
        current_phase.is_current = False
        current_phase.is_completed = True
        current_phase.save(update_fields=['is_current', 'is_completed'])

        next_phase.is_current = True
        next_phase.save(update_fields=['is_current'])

        explanation = (
            f"Avanço concluído da '{current_phase.name}' para a '{next_phase.name}'. "
            f"Critério atendido: adesão de {int(completion_ratio*100)}% ({completed_sessions}/{total_sessions} treinos concluídos). "
            f"Nova estratégia ativada: {next_phase.strategy}. "
            f"Prescrição atualizada para {next_phase.sets_reps_prescription} com intensidade {next_phase.intensity_guidance}."
        )

        PlanAdjustmentLog.objects.create(
            annual_plan=plan,
            date=today,
            action_type='FASE_AVANCO',
            reason=f"Avanço para Fase {next_phase.phase_number}",
            explanation=explanation
        )

        return {
            'success': True,
            'message': f"Avanço com sucesso para {next_phase.name}!"
        }

