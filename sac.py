import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, timedelta, timezone

# ==============================================================================
# 1. CONFIGURAÇÕES GERAIS E AMBIENTE
# ==============================================================================
st.set_page_config(
    page_title="S.A.C. - PET Engenharia Química", 
    layout="wide", 
    page_icon="📝", 
    initial_sidebar_state="expanded"
)

ARQUIVO_DB = "respostas_sac_deq.csv"
ARQUIVO_BACKUP = "_backup_autosave.json"

# ==============================================================================
# 2. ESTILO VISUAL INSTITUCIONAL (CSS)
# ==============================================================================
st.markdown("""
    <style>
    /* RESET E FUNDO */
    .stApp {
        background-color: #ffffff !important;
        font-family: 'Segoe UI', 'Roboto', Helvetica, Arial, sans-serif;
    }

    /* TIPOGRAFIA E CORES */
    h1, h2, h3, h4, h5, h6 {
        color: #002060 !important; /* Azul Institucional Escuro */
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    p, label, span, div, li, .stMarkdown {
        color: #2c3e50 !important; /* Cinza Escuro para leitura */
    }

    /* CABEÇALHO PERSONALIZADO */
    .header-institucional {
        border-bottom: 4px solid #002060;
        padding-bottom: 20px;
        margin-bottom: 30px;
        text-align: center;
    }
    .header-titulo {
        font-size: 2.5rem;
        color: #002060;
        margin: 0;
    }
    .header-subtitulo {
        font-size: 1.2rem;
        color: #555;
        font-weight: 600;
        margin-top: 5px;
    }

    /* ELEMENTOS DE FORMULÁRIO */
    div.stButton > button {
        background-color: #002060 !important;
        color: white !important;
        border-radius: 6px;
        height: 4.5em;
        font-size: 16px;
        font-weight: 700;
        border: none;
        width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        text-transform: uppercase;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #003399 !important;
        transform: translateY(-2px);
    }
    div.stButton > button p {
        color: white !important;
    }

    .stTextInput input, .stTextArea textarea {
        border: 1px solid #ced4da;
        border-radius: 4px;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #002060;
        box-shadow: 0 0 0 1px #002060;
    }

    /* CARD DE PERGUNTA */
    .pergunta-card {
        background-color: #fcfcfc;
        border: 1px solid #e9ecef;
        border-left: 6px solid #002060;
        border-radius: 6px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .pergunta-texto {
        font-size: 1.15rem;
        font-weight: 700;
        color: #002060 !important;
        margin-bottom: 15px;
    }

    /* ABAS DE NAVEGAÇÃO */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 2px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-size: 14px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #f0f4f8 !important;
        border-bottom: 3px solid #002060 !important;
        color: #002060 !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CABEÇALHO INSTITUCIONAL
# ==============================================================================
st.markdown("""
    <div class="header-institucional">
        <div class="header-titulo">S.A.C.</div>
        <div class="header-subtitulo">SISTEMA DE AVALIAÇÃO CURRICULAR</div>
        <div style="font-size: 0.9rem; color: #666; margin-top: 5px;">DEPARTAMENTO DE ENGENHARIA QUÍMICA - UFC</div>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LÓGICA DE GERENCIAMENTO DE ESTADO E HORA
# ==============================================================================
if 'form_key' not in st.session_state:
    st.session_state.form_key = 0

def obter_hora_ceara():
    """Função para pegar a hora certa (UTC-3) independente do servidor."""
    # Pega a hora atual UTC e subtrai 3 horas
    fuso_ceara = timezone(timedelta(hours=-3))
    agora = datetime.now(fuso_ceara)
    return agora.strftime("%Y-%m-%d %H:%M:%S")

def limpar_formulario():
    st.session_state.form_key += 1
    if os.path.exists(ARQUIVO_BACKUP):
        try:
            os.remove(ARQUIVO_BACKUP)
        except:
            pass

def renderizar_pergunta(texto_pergunta, id_unica):
    """Gera o bloco visual da pergunta com Card HTML"""
    with st.container():
        st.markdown(f"""
        <div class="pergunta-card">
            <div class="pergunta-texto">{texto_pergunta}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col_input, col_obs = st.columns([0.60, 0.40])
        
        with col_input:
            val = st.select_slider(
                "Nível de Competência Desenvolvida", 
                options=["0", "1", "2", "3", "4", "5"], 
                value="0", 
                key=f"nota_{id_unica}_{st.session_state.form_key}",
                help="0 = Nenhuma contribuição | 5 = Máxima contribuição"
            )
        
        with col_obs:
            obs = st.text_input(
                "Justificativa e Observações", 
                placeholder="Insira comentários pertinentes...", 
                key=f"obs_{id_unica}_{st.session_state.form_key}"
            )
        
    return int(val), obs

# ==============================================================================
# 5. BARRA LATERAL (IDENTIFICAÇÃO)
# ==============================================================================
respostas = {}

with st.sidebar:
    tab_form, tab_guia = st.tabs(["👤 Identificação", "📘 Guia de Ajuda"])
    
    with tab_form:
        st.markdown("### DADOS DO REGISTRO")
        
        lista_petianos = [
            "", 
            "Ana Carolina",
            "Ana Clara", 
            "Ana Júlia",
            "Eric Rullian", 
            "Gildelandio Junior", 
            "Lucas Mossmann (trainee)",
            "Pedro Paulo"
        ]
        
        respostas["Petiano_Responsavel"] = st.selectbox(
            "Petiano Responsável", 
            lista_petianos,
            key=f"pet_{st.session_state.form_key}"
        )
        
        respostas["Nome"] = st.text_input("Nome Completo do Discente", key=f"nome_{st.session_state.form_key}")
        respostas["Matricula"] = st.text_input("Número de Matrícula", key=f"mat_{st.session_state.form_key}")
        
        lista_semestres = [f"{i}º Semestre" for i in range(1, 11)]
        respostas["Semestre"] = st.selectbox("Semestre Letivo Atual", lista_semestres, key=f"sem_{st.session_state.form_key}")
        
        respostas["Curriculo"] = st.radio(
            "Matriz Curricular", 
            ["Novo (2023.1)", "Antigo (2005.1)"], 
            key=f"curr_{st.session_state.form_key}"
        )
        
        # USA A HORA CORRIGIDA (UTC-3)
        respostas["Data_Registro"] = obter_hora_ceara()
        
        st.markdown("---")
        st.success("✅ Backup Ativo")
        st.caption("Progresso salvo automaticamente.")

    with tab_guia:
        st.markdown("### 📘 GUIA DO AVALIADOR")
        st.info("O objetivo é avaliar o impacto das disciplinas na formação.")
        st.markdown("""
        **Escala (0-5):**
        * **0:** Nenhuma contribuição.
        * **1-2:** Contribuição baixa.
        * **3:** Média.
        * **4-5:** Alta/Excelente contribuição.
        """)

# ==============================================================================
# 6. CONTEÚDO PRINCIPAL (ABAS E QUESTÕES)
# ==============================================================================

abas = [
    "Competências Gerais", 
    "Competências Específicas", 
    "Disciplinas Básicas", 
    "Disciplinas Profissionais", 
    "Disciplinas Avançadas", 
    "Reflexão Final", 
    "📊 Painel Gerencial"
]
tabs = st.tabs(abas)

# --- ABA 1: GERAIS ---
with tabs[0]:
    st.markdown("### 1. COMPETÊNCIAS TÉCNICAS E GERAIS")
    respostas["1. Investigação e Análise"], respostas["Obs_1"] = renderizar_pergunta("1. Projetar e conduzir experimentos e interpretar resultados", "q1")
    respostas["2. Ferramentas e Técnicas"], respostas["Obs_2"] = renderizar_pergunta("2. Desenvolver e/ou utilizar novas ferramentas e técnicas", "q2")
    respostas["3. Concepção de Sistemas"], respostas["Obs_3"] = renderizar_pergunta("3. Conceber, projetar e analisar sistemas, produtos e processos", "q3")
    respostas["4. Resolução de Problemas"], respostas["Obs_4"] = renderizar_pergunta("4. Formular, conceber e avaliar soluções para problemas de engenharia", "q4")
    respostas["5. Modelagem Científica"], respostas["Obs_5"] = renderizar_pergunta("5. Analisar e compreender fenômenos físicos e químicos através de modelos", "q5")
    respostas["6. Comunicação Técnica"], respostas["Obs_6"] = renderizar_pergunta("6. Comunicar-se nas formas escrita, oral e gráfica", "q6")
    respostas["7. Trabalho em Equipe"], respostas["Obs_7"] = renderizar_pergunta("7. Trabalhar e liderar equipes profissionais e multidisciplinares", "q7")
    respostas["8. Ética Profissional"], respostas["Obs_8"] = renderizar_pergunta("8. Aplicar ética e legislação no exercício profissional", "q8")

# --- ABA 2: COMPETÊNCIAS ESPECÍFICAS ---
with tabs[1]:
    st.markdown("### 2. COMPETÊNCIAS ESPECÍFICAS DA ENGENHARIA QUÍMICA")
    respostas["9. Fundamentos Matemáticos"], respostas["Obs_9"] = renderizar_pergunta("9. Aplicar conhecimentos matemáticos, científicos e tecnológicos", "q9")
    respostas["10. Modelagem de Transporte"], respostas["Obs_10"] = renderizar_pergunta("10. Compreender e modelar transferência de quantidade de movimento, calor e massa", "q10")
    respostas["11. Aplicação de Transporte"], respostas["Obs_11"] = renderizar_pergunta("11. Aplicar conhecimentos de fenômenos de transporte ao projeto", "q11")
    respostas["12. Transformação da Matéria"], respostas["Obs_12"] = renderizar_pergunta("12. Compreender mecanismos de transformação da matéria e energia", "q12")
    respostas["13. Processos de Separação"], respostas["Obs_13"] = renderizar_pergunta("13. Projetar sistemas de recuperação, separação e purificação", "q13")
    respostas["14. Cinética Química"], respostas["Obs_14"] = renderizar_pergunta("14. Compreender mecanismos cinéticos de reações químicas", "q14")
    respostas["15. Engenharia de Reatores"], respostas["Obs_15"] = renderizar_pergunta("15. Projetar e otimizar sistemas reacionais e reatores", "q15")
    respostas["16. Controle de Processos"], respostas["Obs_16"] = renderizar_pergunta("16. Projetar sistemas de controle de processos industriais", "q16")
    respostas["17. Projetos Industriais"], respostas["Obs_17"] = renderizar_pergunta("17. Projetar e otimizar plantas industriais (ambiental/segurança)", "q17")
    st.markdown("### EIXOS DE FORMAÇÃO PRÁTICA")
    respostas["18. Projeto Básico"], respostas["Obs_18"] = renderizar_pergunta("18. Aplicação de conhecimentos em projeto básico e dimensionamento", "q18")
    respostas["19. Melhoria de Processos"], respostas["Obs_19"] = renderizar_pergunta("19. Execução de projetos de produção e melhorias de processos", "q19")

# --- ABA 3: DISCIPLINAS BÁSICAS ---
with tabs[2]:
    st.markdown("### 3. DISCIPLINAS DE FORMAÇÃO BÁSICA")
    with st.expander("CÁLCULO DIFERENCIAL E INTEGRAL"):
        respostas["Cálculo: Análise de Dados"], respostas["Obs_Calc1"] = renderizar_pergunta("21. Analisar grandes volumes de dados", "calc_21")
        respostas["Cálculo: Formação Básica"], respostas["Obs_Calc2"] = renderizar_pergunta("52. Formação Básica (cálculo, física, química, estatística)", "calc_52")
    with st.expander("FÍSICA GERAL"):
        respostas["Física: Operação de Sistemas"], respostas["Obs_Fis1"] = renderizar_pergunta("22. Analisar criticamente a operação e manutenção de sistemas", "fis_22")
        respostas["Física: Ciências da Engenharia"], respostas["Obs_Fis2"] = renderizar_pergunta("53. Ciência da Engenharia (mecânica, resistência)", "fis_53")
    with st.expander("QUÍMICA GERAL E ANALÍTICA"):
        respostas["Química: Transformação"], respostas["Obs_Qui1"] = renderizar_pergunta("23. Aplicar conhecimentos de transformação a processos", "qui_23")
        respostas["Química: Desenvolvimento"], respostas["Obs_Qui2"] = renderizar_pergunta("24. Conceber e desenvolver produtos e processos", "qui_24")
    with st.expander("TERMODINÂMICA"):
        respostas["Termodinâmica: Energia"], respostas["Obs_Termo1"] = renderizar_pergunta("25. Projetar sistemas de suprimento energético", "termo_25")
        respostas["Termodinâmica: Ciência EQ"], respostas["Obs_Termo2"] = renderizar_pergunta("54. Ciência da Eng. Química (termodinâmica)", "termo_54")
    with st.expander("FENÔMENOS DE TRANSPORTE E MECÂNICA DOS FLUIDOS"):
        respostas["FT: Aplicação"], respostas["Obs_FT1"] = renderizar_pergunta("26. Aplicar conhecimentos de fenômenos de transporte", "ft_26")
        respostas["FT: Comunicação Gráfica"], respostas["Obs_FT2"] = renderizar_pergunta("27. Comunicar-se tecnicamente e usar recursos gráficos", "ft_27")
        respostas["MecFlu: Soluções"], respostas["Obs_MF1"] = renderizar_pergunta("28. Implantar, implementar e controlar soluções", "mecflu_28")
        respostas["MecFlu: Supervisão"], respostas["Obs_MF2"] = renderizar_pergunta("29. Operar e supervisionar instalações", "mecflu_29")

# --- ABA 4: PROFISSIONAIS ---
with tabs[3]:
    st.markdown("### 4. DISCIPLINAS PROFISSIONALIZANTES")
    with st.expander("OPERAÇÕES UNITÁRIAS (I e II)"):
        respostas["OpUnit: Manutenção"], respostas["Obs_OP1"] = renderizar_pergunta("30. Inspecionar e coordenar manutenção (Sep. Mecânicas)", "op1_30")
        respostas["OpUnit: Tecnologia"], respostas["Obs_OP1b"] = renderizar_pergunta("55. Tecnologia Industrial (Op. Unit, Controle)", "op1_55")
        respostas["OpUnit: Impacto Ambiental"], respostas["Obs_OP2"] = renderizar_pergunta("31. Elaborar estudos de impactos ambientais", "op2_31")
        respostas["OpUnit: Tratamento"], respostas["Obs_OP2b"] = renderizar_pergunta("32. Projetar processos de tratamento ambiental", "op2_32")
    with st.expander("REATORES QUÍMICOS"):
        respostas["Reatores: Recursos"], respostas["Obs_Reat1"] = renderizar_pergunta("33. Gerir recursos estratégicos na produção", "reat_33")
        respostas["Reatores: Qualidade"], respostas["Obs_Reat2"] = renderizar_pergunta("34. Aplicar modelos de produção e controle de qualidade", "reat_34")
    with st.expander("CONTROLE DE PROCESSOS E PROJETOS"):
        respostas["Controle: Supervisão"], respostas["Obs_Ctrl1"] = renderizar_pergunta("35. Controle e supervisão de instalações", "ctrl_35")
        respostas["Controle: Gestão"], respostas["Obs_Ctrl2"] = renderizar_pergunta("36. Gestão de empreendimentos industriais", "ctrl_36")
        respostas["Projetos: Gestão Industrial"], respostas["Obs_Proj1"] = renderizar_pergunta("56. Projetos Industriais e Gestão", "proj_56")
        respostas["Projetos: Ética e Humanidades"], respostas["Obs_Proj2"] = renderizar_pergunta("57. Ética, Meio Ambiente e Humanidades", "proj_57")

# --- ABA 5: DISCIPLINAS AVANÇADAS ---
with tabs[4]:
    st.markdown("### 5. DISCIPLINAS AVANÇADAS E COMPLEMENTARES")
    with st.expander("GESTÃO, ECONOMIA E MEIO AMBIENTE"):
        respostas["Economia: Novos Conceitos"], respostas["Obs_Ec1"] = renderizar_pergunta("37. Engenharia Econômica: Aprender novos conceitos", "econ_37")
        respostas["Economia: Visão Global"], respostas["Obs_Ec2"] = renderizar_pergunta("38. Engenharia Econômica: Visão global", "econ_38")
        respostas["Gestão: Comprometimento"], respostas["Obs_Ges1"] = renderizar_pergunta("39. Gestão da Produção: Comprometimento organizacional", "gest_39")
        respostas["Gestão: Resultados"], respostas["Obs_Ges2"] = renderizar_pergunta("40. Gestão da Produção: Gerar resultados efetivos", "gest_40")
        respostas["Ambiental: Inovação"], respostas["Obs_Amb1"] = renderizar_pergunta("41. Engenharia Ambiental: Inovação", "amb_41")
        respostas["Ambiental: Novas Situações"], respostas["Obs_Amb2"] = renderizar_pergunta("42. Engenharia Ambiental: Lidar com situações novas", "amb_42")
        respostas["Segurança: Incertezas"], respostas["Obs_Seg1"] = renderizar_pergunta("43. Segurança de Processos: Lidar com incertezas", "seg_43")
        respostas["Segurança: Decisão"], respostas["Obs_Seg2"] = renderizar_pergunta("44. Segurança de Processos: Iniciativa e decisão", "seg_44")
    with st.expander("ATIVIDADES PRÁTICAS (LABORATÓRIO E ESTÁGIO)"):
        respostas["Laboratório: Criatividade"], respostas["Obs_Lab1"] = renderizar_pergunta("45. Laboratório de Eng. Química: Criatividade", "lab_45")
        respostas["Laboratório: Relacionamento"], respostas["Obs_Lab2"] = renderizar_pergunta("46. Laboratório de Eng. Química: Relacionamento interpessoal", "lab_46")
        respostas["Estágio: Autocontrole"], respostas["Obs_Est1"] = renderizar_pergunta("47. Estágio Supervisionado: Autocontrole emocional", "est_47")
        respostas["Estágio: Empreendedorismo"], respostas["Obs_Est2"] = renderizar_pergunta("48. Estágio Supervisionado: Capacidade empreendedora", "est_48")
    with st.expander("DISCIPLINAS OPTATIVAS"):
        respostas["Biotecnologia: Dados"], respostas["Obs_Bio1"] = renderizar_pergunta("49. Biotecnologia: Analisar grandes volumes de dados", "bio_49")
        respostas["Biotecnologia: Ferramentas"], respostas["Obs_Bio2"] = renderizar_pergunta("50. Biotecnologia: Novas ferramentas", "bio_50")
        respostas["Petróleo e Gás: Recuperação"], respostas["Obs_Pet1"] = renderizar_pergunta("51. Petróleo e Gás: Projetar sistemas de recuperação", "petro_51")
        respostas["Petróleo e Gás: Reatores"], respostas["Obs_Pet2"] = renderizar_pergunta("52. Petróleo e Gás: Projetar reatores", "petro_52")
        respostas["Polímeros: Cinética"], respostas["Obs_Pol1"] = renderizar_pergunta("53. Polímeros: Mecanismos cinéticos", "poli_53")
        respostas["Polímeros: Produtos"], respostas["Obs_Pol2"] = renderizar_pergunta("54. Polímeros: Conceber produtos", "poli_54")
        respostas["Catálise: Mecanismos"], respostas["Obs_Cat1"] = renderizar_pergunta("55. Catálise: Mecanismos de transformação", "cat_55")
        respostas["Catálise: Produção"], respostas["Obs_Cat2"] = renderizar_pergunta("56. Catálise: Aplicar conhecimentos a produção", "cat_56")
    with st.expander("DISCIPLINAS INTEGRADORAS"):
        respostas["Simulação: Dados"], respostas["Obs_Sim1"] = renderizar_pergunta("57. Simulação de Processos: Analisar grandes volumes de dados", "sim_57")
        respostas["Simulação: Comunicação"], respostas["Obs_Sim2"] = renderizar_pergunta("58. Simulação de Processos: Comunicar-se tecnicamente", "sim_58")
        respostas["Otimização: Soluções"], respostas["Obs_Otim1"] = renderizar_pergunta("59. Otimização de Processos: Soluções para problemas", "otim_59")
        respostas["Otimização: Modelagem"], respostas["Obs_Otim2"] = renderizar_pergunta("60. Otimização de Processos: Modelos de produção", "otim_60")
        respostas["TCC: Comunicação"], respostas["Obs_TCC1"] = renderizar_pergunta("61. Trabalho de Conclusão de Curso: Comunicação escrita/oral", "tcc_61")
        respostas["TCC: Liderança"], respostas["Obs_TCC2"] = renderizar_pergunta("62. Trabalho de Conclusão de Curso: Liderar equipes", "tcc_62")

# --- ABA 6: REFLEXÃO FINAL ---
with tabs[5]:
    st.markdown("### 6. REFLEXÃO FINAL E AUTOAVALIAÇÃO")
    respostas["20. Capacidade de Aprendizado"], respostas["Obs_20"] = renderizar_pergunta("20. Capacidade de aprender rapidamente novos conceitos (Geral)", "q20_indiv")
    st.markdown("#### AUTOAVALIAÇÃO")
    respostas["Autoavaliação: Pontos Fortes"] = st.text_area("Quais competências considera seus pontos fortes?", key=f"fortes_{st.session_state.form_key}")
    respostas["Autoavaliação: Pontos a Desenvolver"] = st.text_area("Quais competências necessitam de maior desenvolvimento?", key=f"fracos_{st.session_state.form_key}")
    st.markdown("#### EXPERIÊNCIA PRÁTICA")
    respostas["Contribuição Prática"] = st.text_area("Como as atividades acadêmicas/profissionais contribuíram?", key=f"prat_{st.session_state.form_key}")
    respostas["Exemplos de Aplicação"] = st.text_area("Cite exemplos concretos onde aplicou competências:", key=f"ex_{st.session_state.form_key}")
    st.markdown("#### PERSPECTIVAS FUTURAS")
    respostas["Competências Essenciais Futuras"] = st.text_area("Quais competências considera essenciais para sua carreira?", key=f"fut1_{st.session_state.form_key}")
    respostas["Plano de Desenvolvimento"] = st.text_area("Como planeja continuar desenvolvendo suas competências?", key=f"fut2_{st.session_state.form_key}")
    respostas["Observações Finais"] = st.text_area("Comentários Finais e Sugestões", key=f"obsf_{st.session_state.form_key}")

    st.markdown("---")
    
    if st.button("💾 REGISTRAR DADOS E REINICIAR FORMULÁRIO", type="primary"):
        if not respostas["Nome"]:
            st.error("⚠️ ERRO: O preenchimento do NOME DO DISCENTE é obrigatório.")
        elif not respostas["Petiano_Responsavel"]:
            st.error("⚠️ ERRO: Selecione o PETIANO RESPONSÁVEL pela aplicação.")
        else:
            try:
                df_new = pd.DataFrame([respostas])
                if os.path.exists(ARQUIVO_DB):
                    df_new.to_csv(ARQUIVO_DB, mode='a', header=False, index=False)
                else:
                    df_new.to_csv(ARQUIVO_DB, mode='w', header=True, index=False)
                
                st.balloons()
                st.success(f"Sucesso! A avaliação do discente {respostas['Nome']} foi registrada na base de dados.")
                limpar_formulario()
                st.rerun()
            except PermissionError:
                st.error("❌ ERRO DE PERMISSÃO: O arquivo 'respostas_sac_deq.csv' está aberto no Excel. Feche o arquivo e tente novamente.")
            except Exception as e:
                st.error(f"❌ ERRO INESPERADO: {e}")

# --- AUTO-SAVE ---
try:
    with open(ARQUIVO_BACKUP, "w", encoding='utf-8') as f:
        json.dump(respostas, f, indent=4, ensure_ascii=False)
except:
    pass

# ==============================================================================
# 8. ABA DASHBOARD (CORRIGIDA)
# ==============================================================================
with tabs[6]:
    st.markdown("### 📊 PAINEL DE INDICADORES DE DESEMPENHO")
    
    if os.path.exists(ARQUIVO_DB):
        try:
            # Lendo com Matrícula como string para não somar
            df = pd.read_csv(ARQUIVO_DB, dtype={'Matricula': str})
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Discentes Avaliados", len(df))
            
            # --- CORREÇÃO DA MÉDIA BUGADA ---
            # Identifica colunas que NÃO são de identificação para calcular média
            colunas_ignorar = [
                'Nome', 'Matricula', 'Semestre', 'Curriculo', 
                'Data_Registro', 'Petiano_Responsavel'
            ]
            # Pega só colunas que não estão na lista de ignorar e não começam com Obs ou Auto
            colunas_numericas = [
                c for c in df.columns 
                if c not in colunas_ignorar 
                and not c.startswith("Obs") 
                and not c.startswith("Auto")
                and not c.startswith("Justificativa") # Garantindo que texto não entra
                and not c.startswith("Contribuição")
                and not c.startswith("Exemplos")
                and not c.startswith("Competências")
                and not c.startswith("Plano")
                and not c.startswith("Comentários")
            ]

            # Converte para numérico (garantia)
            df_num = df[colunas_numericas].apply(pd.to_numeric, errors='coerce')
            
            if not df_num.empty:
                media_geral = df_num.mean().mean()
                col2.metric("Média Geral de Competências", f"{media_geral:.2f}/5.0")
            
            # --- CORREÇÃO DA DATA CONFUSA ---
            if 'Data_Registro' in df.columns:
                last_dt = pd.to_datetime(df['Data_Registro']).max()
                # Formato Brasileiro: Dia/Mês/Ano às Hora:Minuto
                data_formatada = last_dt.strftime("%d/%m/%Y às %H:%M")
                col3.metric("Última Atualização do Banco", data_formatada)
            
            st.markdown("---")

            st.markdown("#### Base de Dados Detalhada (Registro Geral)")
            # Tabela Simples (Sem cores/gradiente para evitar erros de biblioteca)
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar Tabela Completa (Excel/CSV)", 
                data=csv, 
                file_name=f"relatorio_sac_{datetime.now().strftime('%Y%m%d')}.csv", 
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Erro ao ler o banco de dados: {e}")
    else:
        st.info("Ainda não há dados registrados no sistema. Realize o primeiro preenchimento para visualizar os indicadores.")
