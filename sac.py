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
# 2. ESTILO VISUAL RESPONSIVO (MODO CLARO E ESCURO)
# ==============================================================================
st.markdown("""
    <style>
    /* VARIÁVEIS DE COR E TIPO */
    :root {
        --primary-color: #002060; /* Azul Institucional */
        --secondary-color: #f0f2f6;
    }

    /* AJUSTES GERAIS DE FONTE E COR */
    .stApp { font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; }
    
    /* TÍTULOS (Adaptáveis ao tema) */
    h1, h2, h3, h4 {
        color: var(--primary-color) !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* MODO ESCURO - AJUSTE DE TÍTULOS PARA LEITURA */
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, h4 { color: #82b1ff !important; }
    }

    /* CARD DA PERGUNTA (CONTAINER) */
    .pergunta-card {
        background-color: rgba(255, 255, 255, 0.05); /* Transparente adaptável */
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-left: 5px solid #002060;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    /* No modo escuro, a borda esquerda muda para azul claro para destacar */
    @media (prefers-color-scheme: dark) {
        .pergunta-card { border-left: 5px solid #82b1ff; }
    }

    .pergunta-texto {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 15px;
        opacity: 0.95;
    }

    /* BOTÕES DE NAVEGAÇÃO */
    .stButton button {
        border-radius: 6px;
        font-weight: 700;
        text-transform: uppercase;
        height: 3.5em;
        transition: 0.3s;
        width: 100%;
    }
    
    /* BOTÃO "PRÓXIMO" (Estilo Secundário) */
    div[data-testid="stVerticalBlock"] > div > div > div > div > .stButton button {
        border: 2px solid #002060;
        color: #002060;
        background-color: transparent;
    }
    div[data-testid="stVerticalBlock"] > div > div > div > div > .stButton button:hover {
        background-color: #002060;
        color: white;
    }

    /* BOTÃO "FINALIZAR" (Estilo Primário) */
    .botao-final button {
        background-color: #002060 !important;
        color: white !important;
        border: none;
        height: 4.5em;
        font-size: 1.1rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .botao-final button:hover {
        background-color: #003399 !important;
        transform: scale(1.01);
    }

    /* MENUS DO STREAMLIT */
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CABEÇALHO INSTITUCIONAL
# ==============================================================================
st.markdown("""
    <div style="text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid rgba(128,128,128,0.2);">
        <h1 style="margin: 0; font-size: 2.5rem;">S.A.C.</h1>
        <div style="font-size: 1.2rem; font-weight: 600; opacity: 0.8;">SISTEMA DE AVALIAÇÃO CURRICULAR - MÓDULO DE TRANSCRIÇÃO</div>
        <div style="font-size: 0.9rem; opacity: 0.6; margin-top: 5px;">PET ENGENHARIA QUÍMICA - UNIVERSIDADE FEDERAL DO CEARÁ</div>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. GERENCIAMENTO DE ESTADO E NAVEGAÇÃO
# ==============================================================================
# Lista ordenada das seções para a navegação funcionar
SECOES = [
    "1. Competências Gerais", 
    "2. Competências Específicas", 
    "3. Disciplinas Básicas", 
    "4. Disciplinas Profissionais", 
    "5. Disciplinas Avançadas", 
    "6. Reflexão Final (Obrigatória)", 
    "📊 Painel Gerencial"
]

if 'form_key' not in st.session_state:
    st.session_state.form_key = 0

# Inicializa a navegação na primeira página
if 'navegacao_atual' not in st.session_state:
    st.session_state.navegacao_atual = SECOES[0]

def navegar_proxima():
    """Avança para a próxima aba e salva backup."""
    try:
        indice = SECOES.index(st.session_state.navegacao_atual)
        if indice < len(SECOES) - 1:
            st.session_state.navegacao_atual = SECOES[indice + 1]
            # Força recarregamento para mudar a aba visualmente
            st.rerun()
    except:
        pass

def limpar_formulario():
    st.session_state.form_key += 1
    st.session_state.navegacao_atual = SECOES[0] # Volta para o início
    if os.path.exists(ARQUIVO_BACKUP):
        try: os.remove(ARQUIVO_BACKUP)
        except: pass

def obter_hora_ceara():
    """Garante horário local UTC-3."""
    fuso = timezone(timedelta(hours=-3))
    return datetime.now(fuso).strftime("%Y-%m-%d %H:%M:%S")

def renderizar_pergunta(texto_pergunta, id_unica):
    """
    Renderiza o bloco de pergunta com opção N/A.
    """
    with st.container():
        st.markdown(f"""<div class="pergunta-card"><div class="pergunta-texto">{texto_pergunta}</div></div>""", unsafe_allow_html=True)
        
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            # Opções incluindo N/A
            opcoes_nota = ["N/A", "0", "1", "2", "3", "4", "5"]
            val = st.select_slider(
                "Nível de Competência (0-5)", 
                options=opcoes_nota, 
                value="0", # Padrão
                key=f"nota_{id_unica}_{st.session_state.form_key}",
                help="Selecione 'N/A' se o aluno não respondeu ou rasurou."
            )
        with c2:
            obs = st.text_input(
                "Observações de Transcrição", 
                placeholder="Transcreva comentários se houver...", 
                key=f"obs_{id_unica}_{st.session_state.form_key}"
            )
    
    # Tratamento do retorno: Se for N/A, retorna string, senão retorna inteiro
    return val, obs

# ==============================================================================
# 5. BARRA LATERAL (IDENTIFICAÇÃO)
# ==============================================================================
respostas = {}

with st.sidebar:
    tab_dados, tab_ajuda = st.tabs(["👤 Identificação", "📘 Guia de Ajuda"])
    
    # --- ABA DADOS ---
    with tab_dados:
        st.markdown("### REGISTRO DO FORMULÁRIO")
        st.info("Preencha conforme o papel físico.")
        
        lista_petianos = sorted([
            "",
            "Ana Carolina", "Ana Clara", "Ana Júlia", 
            "Eric Rullian", "Gildelandio Junior", 
            "Lucas Mossmann (trainee)", "Pedro Paulo"
        ])
        
        respostas["Petiano_Responsavel"] = st.selectbox(
            "Responsável pela Transcrição", 
            lista_petianos,
            key=f"pet_{st.session_state.form_key}"
        )
        
        respostas["Nome"] = st.text_input("Nome do Discente (Legível)", key=f"nome_{st.session_state.form_key}")
        respostas["Matricula"] = st.text_input("Matrícula", key=f"mat_{st.session_state.form_key}")
        
        lista_semestres = [f"{i}º Semestre" for i in range(1, 11)]
        respostas["Semestre"] = st.selectbox("Semestre Indicado", lista_semestres, key=f"sem_{st.session_state.form_key}")
        
        respostas["Curriculo"] = st.radio("Matriz Curricular", ["Novo (2023.1)", "Antigo (2005.1)"], key=f"curr_{st.session_state.form_key}")
        respostas["Data_Registro"] = obter_hora_ceara()
        
        st.markdown("---")
        st.success("✅ Sistema Online")

    # --- ABA AJUDA (ATUALIZADA) ---
    with tab_ajuda:
        st.markdown("### 📘 MANUAL DE TRANSCRIÇÃO")
        
        st.markdown("#### 1. SOBRE A OPÇÃO 'N/A'")
        st.info("""
        Utilize a opção **N/A (Não se Aplica)** no slider quando:
        * O aluno deixou a questão em branco.
        * O aluno marcou duas opções simultaneamente (anulado).
        * A resposta está rasurada/ilegível.
        
        *Nota: O 'N/A' não conta como zero na média final.*
        """)
        
        st.markdown("#### 2. TRANSCRIÇÃO DE TEXTO")
        st.markdown("""
        * Digite exatamente o que está escrito (**ipsis litteris**).
        * Se houver erros de português no papel, mantenha-os (fidelidade).
        * Se ilegível, digite: `[Texto ilegível]`.
        """)
        
        st.markdown("#### 3. CAMPOS OBRIGATÓRIOS")
        st.error("""
        A seção **REFLEXÃO FINAL** não pode ficar vazia.
        Se o aluno não escreveu nada, você deve digitar: **"EM BRANCO"**.
        O sistema bloqueará o salvamento se esses campos estiverem vazios.
        """)

# ==============================================================================
# 6. MENU DE NAVEGAÇÃO SUPERIOR (WIZARD)
# ==============================================================================
# Cria um menu de "Radio Buttons" horizontal que simula abas, mas permite controle via código
secao_ativa = st.radio(
    "Navegação Rápida", 
    SECOES, 
    horizontal=True, 
    key="navegacao_atual",
    label_visibility="collapsed"
)

st.markdown("---")

# ==============================================================================
# 7. CONTEÚDO DAS SEÇÕES
# ==============================================================================

# --- SEÇÃO 1 ---
if secao_ativa == SECOES[0]:
    st.markdown("### 1. COMPETÊNCIAS TÉCNICAS E GERAIS")
    respostas["1. Investigação"], respostas["Obs_1"] = renderizar_pergunta("1. Projetar e conduzir experimentos e interpretar resultados", "q1")
    respostas["2. Ferramentas"], respostas["Obs_2"] = renderizar_pergunta("2. Desenvolver e/ou utilizar novas ferramentas e técnicas", "q2")
    respostas["3. Concepção"], respostas["Obs_3"] = renderizar_pergunta("3. Conceber, projetar e analisar sistemas, produtos e processos", "q3")
    respostas["4. Resolução Prob."], respostas["Obs_4"] = renderizar_pergunta("4. Formular, conceber e avaliar soluções para problemas de engenharia", "q4")
    respostas["5. Modelagem"], respostas["Obs_5"] = renderizar_pergunta("5. Analisar e compreender fenômenos físicos e químicos através de modelos", "q5")
    respostas["6. Comunicação"], respostas["Obs_6"] = renderizar_pergunta("6. Comunicar-se nas formas escrita, oral e gráfica", "q6")
    respostas["7. Trab. Equipe"], respostas["Obs_7"] = renderizar_pergunta("7. Trabalhar e liderar equipes profissionais e multidisciplinares", "q7")
    respostas["8. Ética"], respostas["Obs_8"] = renderizar_pergunta("8. Aplicar ética e legislação no exercício profissional", "q8")
    
    st.markdown("---")
    col1, col2 = st.columns([0.8, 0.2])
    with col2: st.button("PRÓXIMA SEÇÃO ➡️", on_click=navegar_proxima, key="btn_1")

# --- SEÇÃO 2 ---
elif secao_ativa == SECOES[1]:
    st.markdown("### 2. COMPETÊNCIAS ESPECÍFICAS DA ENGENHARIA QUÍMICA")
    respostas["9. Fundamentos Mat."], respostas["Obs_9"] = renderizar_pergunta("9. Aplicar conhecimentos matemáticos, científicos e tecnológicos", "q9")
    respostas["10. Modelagem Transp."], respostas["Obs_10"] = renderizar_pergunta("10. Compreender e modelar transferência de quantidade de movimento, calor e massa", "q10")
    respostas["11. Aplic. Transp."], respostas["Obs_11"] = renderizar_pergunta("11. Aplicar conhecimentos de fenômenos de transporte ao projeto", "q11")
    respostas["12. Transf. Matéria"], respostas["Obs_12"] = renderizar_pergunta("12. Compreender mecanismos de transformação da matéria e energia", "q12")
    respostas["13. Separação"], respostas["Obs_13"] = renderizar_pergunta("13. Projetar sistemas de recuperação, separação e purificação", "q13")
    respostas["14. Cinética"], respostas["Obs_14"] = renderizar_pergunta("14. Compreender mecanismos cinéticos de reações químicas", "q14")
    respostas["15. Reatores"], respostas["Obs_15"] = renderizar_pergunta("15. Projetar e otimizar sistemas reacionais e reatores", "q15")
    respostas["16. Controle"], respostas["Obs_16"] = renderizar_pergunta("16. Projetar sistemas de controle de processos industriais", "q16")
    respostas["17. Projetos Ind."], respostas["Obs_17"] = renderizar_pergunta("17. Projetar e otimizar plantas industriais (ambiental/segurança)", "q17")
    st.markdown("#### Eixos de Formação Prática")
    respostas["18. Projeto Básico"], respostas["Obs_18"] = renderizar_pergunta("18. Aplicação de conhecimentos em projeto básico e dimensionamento", "q18")
    respostas["19. Melhoria Proc."], respostas["Obs_19"] = renderizar_pergunta("19. Execução de projetos de produção e melhorias de processos", "q19")
    
    st.markdown("---")
    col1, col2 = st.columns([0.8, 0.2])
    with col2: st.button("PRÓXIMA SEÇÃO ➡️", on_click=navegar_proxima, key="btn_2")

# --- SEÇÃO 3 ---
elif secao_ativa == SECOES[2]:
    st.markdown("### 3. DISCIPLINAS DE FORMAÇÃO BÁSICA")
    with st.expander("CÁLCULO DIFERENCIAL E INTEGRAL", expanded=True):
        respostas["Cálculo: Dados"], respostas["Obs_C1"] = renderizar_pergunta("21. Analisar grandes volumes de dados", "calc_21")
        respostas["Cálculo: Formação"], respostas["Obs_C2"] = renderizar_pergunta("52. Formação Básica", "calc_52")
    with st.expander("FÍSICA GERAL", expanded=True):
        respostas["Física: Operação"], respostas["Obs_F1"] = renderizar_pergunta("22. Analisar criticamente a operação e manutenção de sistemas", "fis_22")
        respostas["Física: Ciência"], respostas["Obs_F2"] = renderizar_pergunta("53. Ciência da Engenharia", "fis_53")
    with st.expander("QUÍMICA GERAL E ANALÍTICA", expanded=True):
        respostas["Química: Transf."], respostas["Obs_Q1"] = renderizar_pergunta("23. Aplicar conhecimentos de transformação a processos", "qui_23")
        respostas["Química: Desenv."], respostas["Obs_Q2"] = renderizar_pergunta("24. Conceber e desenvolver produtos e processos", "qui_24")
    with st.expander("TERMODINÂMICA", expanded=True):
        respostas["Termo: Energia"], respostas["Obs_T1"] = renderizar_pergunta("25. Projetar sistemas de suprimento energético", "termo_25")
        respostas["Termo: Ciência"], respostas["Obs_T2"] = renderizar_pergunta("54. Ciência da Eng. Química", "termo_54")
    with st.expander("FENÔMENOS DE TRANSPORTE E MECÂNICA DOS FLUIDOS", expanded=True):
        respostas["FT: Aplicação"], respostas["Obs_FT1"] = renderizar_pergunta("26. Aplicar conhecimentos de fenômenos de transporte", "ft_26")
        respostas["FT: Gráficos"], respostas["Obs_FT2"] = renderizar_pergunta("27. Comunicar-se tecnicamente e usar recursos gráficos", "ft_27")
        respostas["MecFlu: Soluções"], respostas["Obs_MF1"] = renderizar_pergunta("28. Implantar, implementar e controlar soluções", "mecflu_28")
        respostas["MecFlu: Supervisão"], respostas["Obs_MF2"] = renderizar_pergunta("29. Operar e supervisionar instalações", "mecflu_29")
    
    st.markdown("---")
    col1, col2 = st.columns([0.8, 0.2])
    with col2: st.button("PRÓXIMA SEÇÃO ➡️", on_click=navegar_proxima, key="btn_3")

# --- SEÇÃO 4 ---
elif secao_ativa == SECOES[3]:
    st.markdown("### 4. DISCIPLINAS PROFISSIONALIZANTES")
    with st.expander("OPERAÇÕES UNITÁRIAS (I e II)", expanded=True):
        respostas["OpUnit: Manutenção"], respostas["Obs_O1"] = renderizar_pergunta("30. Inspecionar e coordenar manutenção", "op1_30")
        respostas["OpUnit: Tecnologia"], respostas["Obs_O1b"] = renderizar_pergunta("55. Tecnologia Industrial", "op1_55")
        respostas["OpUnit: Impacto"], respostas["Obs_O2"] = renderizar_pergunta("31. Elaborar estudos de impactos ambientais", "op2_31")
        respostas["OpUnit: Tratamento"], respostas["Obs_O2b"] = renderizar_pergunta("32. Projetar processos de tratamento ambiental", "op2_32")
    with st.expander("REATORES QUÍMICOS", expanded=True):
        respostas["Reatores: Recursos"], respostas["Obs_R1"] = renderizar_pergunta("33. Gerir recursos estratégicos na produção", "reat_33")
        respostas["Reatores: Qualidade"], respostas["Obs_R2"] = renderizar_pergunta("34. Aplicar modelos de produção e controle de qualidade", "reat_34")
    with st.expander("CONTROLE DE PROCESSOS E PROJETOS", expanded=True):
        respostas["Controle: Supervisão"], respostas["Obs_Ct1"] = renderizar_pergunta("35. Controle e supervisão de instalações", "ctrl_35")
        respostas["Controle: Gestão"], respostas["Obs_Ct2"] = renderizar_pergunta("36. Gestão de empreendimentos industriais", "ctrl_36")
        respostas["Projetos: Gestão"], respostas["Obs_Pr1"] = renderizar_pergunta("56. Projetos Industriais e Gestão", "proj_56")
        respostas["Projetos: Ética"], respostas["Obs_Pr2"] = renderizar_pergunta("57. Ética, Meio Ambiente e Humanidades", "proj_57")
    
    st.markdown("---")
    col1, col2 = st.columns([0.8, 0.2])
    with col2: st.button("PRÓXIMA SEÇÃO ➡️", on_click=navegar_proxima, key="btn_4")

# --- SEÇÃO 5 ---
elif secao_ativa == SECOES[4]:
    st.markdown("### 5. DISCIPLINAS AVANÇADAS E COMPLEMENTARES")
    with st.expander("GESTÃO, ECONOMIA E MEIO AMBIENTE", expanded=True):
        respostas["Econ: Novos"], respostas["Obs_Ec1"] = renderizar_pergunta("37. Eng. Econômica: Aprender novos conceitos", "econ_37")
        respostas["Econ: Visão"], respostas["Obs_Ec2"] = renderizar_pergunta("38. Eng. Econômica: Visão global", "econ_38")
        respostas["Gestão: Compr."], respostas["Obs_G1"] = renderizar_pergunta("39. Gestão da Produção: Comprometimento", "gest_39")
        respostas["Gestão: Result."], respostas["Obs_G2"] = renderizar_pergunta("40. Gestão da Produção: Resultados", "gest_40")
        respostas["Amb: Inovação"], respostas["Obs_A1"] = renderizar_pergunta("41. Eng. Ambiental: Inovação", "amb_41")
        respostas["Amb: Situações"], respostas["Obs_A2"] = renderizar_pergunta("42. Eng. Ambiental: Situações novas", "amb_42")
        respostas["Seg: Incertezas"], respostas["Obs_S1"] = renderizar_pergunta("43. Segurança de Processos: Lidar com incertezas", "seg_43")
        respostas["Seg: Decisão"], respostas["Obs_S2"] = renderizar_pergunta("44. Segurança de Processos: Iniciativa e decisão", "seg_44")
    with st.expander("ATIVIDADES PRÁTICAS (LABORATÓRIO E ESTÁGIO)", expanded=True):
        respostas["Lab: Criatividade"], respostas["Obs_L1"] = renderizar_pergunta("45. Laboratório: Criatividade", "lab_45")
        respostas["Lab: Relacionam."], respostas["Obs_L2"] = renderizar_pergunta("46. Laboratório: Relacionamento", "lab_46")
        respostas["Estágio: Autocont."], respostas["Obs_E1"] = renderizar_pergunta("47. Estágio: Autocontrole emocional", "est_47")
        respostas["Estágio: Empreend."], respostas["Obs_E2"] = renderizar_pergunta("48. Estágio: Capacidade empreendedora", "est_48")
    with st.expander("DISCIPLINAS OPTATIVAS", expanded=True):
        respostas["Biotec: Dados"], respostas["Obs_B1"] = renderizar_pergunta("49. Biotecnologia: Analisar grandes volumes de dados", "bio_49")
        respostas["Biotec: Ferram."], respostas["Obs_B2"] = renderizar_pergunta("50. Biotecnologia: Novas ferramentas", "bio_50")
        respostas["Petro: Recuper."], respostas["Obs_P1"] = renderizar_pergunta("51. Petróleo e Gás: Projetar recuperação", "petro_51")
        respostas["Petro: Reatores"], respostas["Obs_P2"] = renderizar_pergunta("52. Petróleo e Gás: Projetar reatores", "petro_52")
        respostas["Poli: Cinética"], respostas["Obs_Po1"] = renderizar_pergunta("53. Polímeros: Mecanismos cinéticos", "poli_53")
        respostas["Poli: Produtos"], respostas["Obs_Po2"] = renderizar_pergunta("54. Polímeros: Conceber produtos", "poli_54")
        respostas["Cat: Mecanismos"], respostas["Obs_Ca1"] = renderizar_pergunta("55. Catálise: Mecanismos de transformação", "cat_55")
        respostas["Cat: Produção"], respostas["Obs_Ca2"] = renderizar_pergunta("56. Catálise: Aplicar na produção", "cat_56")
    with st.expander("DISCIPLINAS INTEGRADORAS", expanded=True):
        respostas["Sim: Dados"], respostas["Obs_Si1"] = renderizar_pergunta("57. Simulação: Analisar dados", "sim_57")
        respostas["Sim: Comun."], respostas["Obs_Si2"] = renderizar_pergunta("58. Simulação: Comunicação técnica", "sim_58")
        respostas["Otim: Soluções"], respostas["Obs_Ot1"] = renderizar_pergunta("59. Otimização: Soluções para problemas", "otim_59")
        respostas["Otim: Modelos"], respostas["Obs_Ot2"] = renderizar_pergunta("60. Otimização: Modelos de produção", "otim_60")
        respostas["TCC: Comun."], respostas["Obs_Tc1"] = renderizar_pergunta("61. TCC: Comunicação escrita/oral", "tcc_61")
        respostas["TCC: Liderança"], respostas["Obs_Tc2"] = renderizar_pergunta("62. TCC: Liderar equipes", "tcc_62")
    
    st.markdown("---")
    col1, col2 = st.columns([0.8, 0.2])
    with col2: st.button("PRÓXIMA SEÇÃO ➡️", on_click=navegar_proxima, key="btn_5")

# --- SEÇÃO 6: REFLEXÃO FINAL (OBRIGATÓRIA) ---
elif secao_ativa == SECOES[5]:
    st.markdown("### 6. REFLEXÃO FINAL E AUTOAVALIAÇÃO")
    st.warning("⚠️ **ATENÇÃO:** Esta seção é de preenchimento OBRIGATÓRIO. Se o aluno deixou em branco, digite 'EM BRANCO'.")
    
    respostas["20. Capacidade de Aprendizado"], respostas["Obs_20"] = renderizar_pergunta("20. Capacidade de aprender rapidamente novos conceitos (Geral)", "q20_indiv")
    
    st.markdown("#### TRANSCRIÇÃO DAS RESPOSTAS ABERTAS")
    
    respostas["Autoavaliação: Pontos Fortes"] = st.text_area("Pontos Fortes (Obrigatório)", key=f"fortes_{st.session_state.form_key}")
    respostas["Autoavaliação: Pontos a Desenvolver"] = st.text_area("Pontos a Desenvolver (Obrigatório)", key=f"fracos_{st.session_state.form_key}")
    
    respostas["Contribuição Prática"] = st.text_area("Contribuição das atividades", key=f"prat_{st.session_state.form_key}")
    respostas["Exemplos de Aplicação"] = st.text_area("Exemplos de aplicação", key=f"ex_{st.session_state.form_key}")
    respostas["Competências Futuras"] = st.text_area("Competências essenciais futuras", key=f"fut1_{st.session_state.form_key}")
    respostas["Plano de Desenvolvimento"] = st.text_area("Plano de desenvolvimento", key=f"fut2_{st.session_state.form_key}")
    respostas["Observações Finais"] = st.text_area("Comentários Finais", key=f"obsf_{st.session_state.form_key}")

    st.markdown("---")
    st.markdown('<div class="botao-final">', unsafe_allow_html=True)
    if st.button("💾 FINALIZAR TRANSCRIÇÃO", type="primary"):
        # VALIDAÇÃO DE OBRIGATORIEDADE
        erros = []
        if not respostas["Nome"]: erros.append("Nome do Discente")
        if not respostas["Petiano_Responsavel"]: erros.append("Petiano Responsável")
        if not respostas["Autoavaliação: Pontos Fortes"] or not respostas["Autoavaliação: Pontos a Desenvolver"]:
            erros.append("Campos de Texto da Seção Final (Digite 'Em Branco' se necessário)")

        if erros:
            st.error(f"❌ IMPOSSÍVEL SALVAR. Preencha os seguintes campos obrigatórios: {', '.join(erros)}")
        else:
            try:
                df_new = pd.DataFrame([respostas])
                if os.path.exists(ARQUIVO_DB):
                    df_new.to_csv(ARQUIVO_DB, mode='a', header=False, index=False)
                else:
                    df_new.to_csv(ARQUIVO_DB, mode='w', header=True, index=False)
                
                st.balloons()
                st.success(f"✅ Transcrição do aluno {respostas['Nome']} finalizada com sucesso!")
                limpar_formulario()
                st.rerun()
            except PermissionError:
                st.error("❌ ERRO: O Excel está aberto. Feche-o e tente novamente.")
            except Exception as e:
                st.error(f"❌ ERRO INESPERADO: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- AUTO-SAVE ---
try:
    with open(ARQUIVO_BACKUP, "w", encoding='utf-8') as f:
        json.dump(respostas, f, indent=4, ensure_ascii=False)
except: pass

# ==============================================================================
# 7. DASHBOARD (PAINEL GERENCIAL)
# ==============================================================================
elif secao_ativa == SECOES[6]:
    st.markdown("### 📊 STATUS DA DIGITALIZAÇÃO")
    
    if os.path.exists(ARQUIVO_DB):
        try:
            # Lê forçando Matrícula como texto para não somar
            df = pd.read_csv(ARQUIVO_DB, dtype={'Matricula': str})
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Formulários Digitados", len(df))
            
            # --- CÁLCULO DA MÉDIA (IGNORANDO 'N/A' e DADOS DE IDENTIFICAÇÃO) ---
            cols_ignorar = [
                'Nome', 'Matricula', 'Semestre', 'Curriculo', 
                'Data_Registro', 'Petiano_Responsavel', 
                'Autoavaliação: Pontos Fortes', 'Autoavaliação: Pontos a Desenvolver'
            ]
            # Seleciona apenas colunas que não estão na lista de ignorar e não são textos de Obs
            cols_calc = [
                c for c in df.columns 
                if c not in cols_ignorar 
                and not c.startswith("Obs") 
                and not c.startswith("Contribuição") 
                and not c.startswith("Exemplos") 
                and not c.startswith("Competências") 
                and not c.startswith("Plano") 
                and not c.startswith("Comentários")
            ]
            
            # Converte "N/A" para NaN (Not a Number) automaticamente
            df_numeric = df[cols_calc].apply(pd.to_numeric, errors='coerce')
            
            if not df_numeric.empty:
                media_geral = df_numeric.mean().mean()
                c2.metric("Média Geral (Notas Válidas)", f"{media_geral:.2f}/5.0")
            
            if 'Data_Registro' in df.columns:
                last = pd.to_datetime(df['Data_Registro']).max()
                c3.metric("Último Registro", last.strftime("%d/%m/%Y às %H:%M"))
            
            st.markdown("---")
            st.markdown("#### Conferência de Dados (Tabela Geral)")
            st.dataframe(df, use_container_width=True, height=500)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar Dados Completos (Backup Excel)", 
                data=csv, 
                file_name=f"sac_backup_{datetime.now().strftime('%Y%m%d')}.csv", 
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Erro ao carregar banco de dados: {e}")
    else:
        st.info("Nenhum formulário digitalizado até o momento.")
