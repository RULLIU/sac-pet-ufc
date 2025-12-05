import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, timedelta, timezone

# ==============================================================================
# 1. CONFIGURAÇÕES GERAIS
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
# 2. ESTILO VISUAL AVANÇADO (RESPONSIVO E INSTITUCIONAL)
# ==============================================================================
st.markdown("""
    <style>
    /* VARIÁVEIS GERAIS */
    :root {
        --primary-color: #002060; /* Azul Institucional PET/UFC */
        --accent-color: #dba800; /* Dourado UFC */
    }

    /* TIPOGRAFIA E BASE */
    .stApp { font-family: 'Segoe UI', 'Roboto', sans-serif; }
    
    /* TÍTULOS ADAPTÁVEIS */
    h1, h2, h3, h4 {
        color: var(--primary-color) !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* MODO ESCURO (DARK MODE) - AJUSTES DE CONTRASTE */
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, h4 { color: #82b1ff !important; } /* Azul claro para leitura */
        .pergunta-card { 
            background-color: #1e1e1e !important; 
            border: 1px solid #333 !important; 
            border-left: 5px solid #82b1ff !important;
        }
        .botao-avancar button {
            border: 2px solid #82b1ff !important;
            color: #82b1ff !important;
        }
        .botao-avancar button:hover {
            background-color: #82b1ff !important;
            color: #000 !important;
        }
        .manual-box { background-color: #262730 !important; border: 1px solid #444 !important; }
    }

    /* MODO CLARO (LIGHT MODE) */
    @media (prefers-color-scheme: light) {
        .stApp { background-color: #ffffff !important; }
        .pergunta-card { 
            background-color: #f8f9fa !important; 
            border: 1px solid #e0e0e0 !important;
            border-left: 5px solid #002060 !important;
        }
        .manual-box { background-color: #f0f2f6 !important; border: 1px solid #ddd !important; }
    }

    /* CARD DA PERGUNTA (CONTAINER) */
    .pergunta-card {
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
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
        transition: all 0.3s ease;
        width: 100%;
    }
    
    /* Estilo Botão "Próximo" */
    .botao-avancar button {
        background-color: transparent;
        border: 2px solid #002060;
        color: #002060;
    }
    .botao-avancar button:hover {
        background-color: #002060;
        color: white;
        transform: translateX(5px);
    }

    /* Estilo Botão "Finalizar" */
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
        transform: scale(1.02);
    }

    /* CAIXAS DO MANUAL */
    .manual-box {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }

    /* Ocultar menus padrão */
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
# 4. GERENCIAMENTO DE ESTADO E LÓGICA
# ==============================================================================
SECOES = [
    "1. Competências Gerais", 
    "2. Competências Específicas", 
    "3. Disciplinas Básicas", 
    "4. Disciplinas Profissionais", 
    "5. Disciplinas Avançadas", 
    "6. Reflexão Final (Obrigatória)", 
    "📊 Painel Gerencial"
]

# Inicialização de Variáveis de Estado
if 'form_key' not in st.session_state: st.session_state.form_key = 0
if 'navegacao_atual' not in st.session_state: st.session_state.navegacao_atual = SECOES[0]

def auto_save():
    """Salva o estado atual em um arquivo JSON local."""
    try:
        with open(ARQUIVO_BACKUP, "w", encoding='utf-8') as f:
            # Filtra apenas dados primitivos para evitar erro
            dados = {k:v for k,v in st.session_state.items() if isinstance(v, (str, int, float, bool))}
            json.dump(dados, f, indent=4, ensure_ascii=False)
    except: pass

def navegar_proxima():
    """Avança para a próxima seção e aciona o Auto-Save."""
    try:
        idx = SECOES.index(st.session_state.navegacao_atual)
        if idx < len(SECOES) - 1:
            st.session_state.navegacao_atual = SECOES[idx + 1]
            auto_save() 
            st.rerun()
    except: pass

def limpar_formulario():
    st.session_state.form_key += 1
    st.session_state.navegacao_atual = SECOES[0]
    if os.path.exists(ARQUIVO_BACKUP):
        try: os.remove(ARQUIVO_BACKUP)
        except: pass

def obter_hora_ceara():
    fuso = timezone(timedelta(hours=-3))
    return datetime.now(fuso).strftime("%Y-%m-%d %H:%M:%S")

def renderizar_pergunta(texto_pergunta, id_unica, valor_padrao="N/A", obs_padrao="", key_suffix=""):
    """
    Renderiza o bloco de pergunta com suporte a 'N/A' e Edição.
    """
    with st.container():
        st.markdown(f"""<div class="pergunta-card"><div class="pergunta-texto">{texto_pergunta}</div></div>""", unsafe_allow_html=True)
        
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            opcoes = ["N/A", "0", "1", "2", "3", "4", "5"]
            val = st.select_slider(
                "Nível de Competência", 
                options=opcoes, 
                value=str(valor_padrao), 
                key=f"nota_{id_unica}{key_suffix}",
                help="Selecione 'N/A' se vazio."
            )
        with c2:
            obs = st.text_input(
                "Observações de Transcrição", 
                value=str(obs_padrao) if pd.notna(obs_padrao) else "",
                placeholder="Transcrição...", 
                key=f"obs_{id_unica}{key_suffix}"
            )
            
    return val, obs

# ==============================================================================
# 5. BARRA LATERAL (IDENTIFICAÇÃO E MANUAL)
# ==============================================================================
respostas = {}

with st.sidebar:
    st.markdown("### ⚙️ MODO DE OPERAÇÃO")
    modo_operacao = st.radio(
        "Selecione:",
        ["📝 Nova Transcrição", "✏️ Editar Registro", "📊 Painel Gerencial"],
        label_visibility="collapsed"
    )
    st.markdown("---")

    if modo_operacao == "📝 Nova Transcrição":
        tab_dados, tab_ajuda = st.tabs(["👤 Identificação", "📘 Manual"])
        
        with tab_dados:
            st.info("Preencha conforme o papel físico.")
            
            lista_petianos = sorted([
                "", "Ana Carolina", "Ana Clara", "Ana Júlia", 
                "Eric Rullian", "Gildelandio Junior", 
                "Lucas Mossmann (trainee)", "Pedro Paulo"
            ])
            
            # Chaves dinâmicas para permitir limpeza do form
            ks = st.session_state.form_key
            respostas["Petiano_Responsavel"] = st.selectbox("Responsável pela Transcrição", lista_petianos, key=f"pet_{ks}")
            respostas["Nome"] = st.text_input("Nome do Discente", key=f"nome_{ks}")
            respostas["Matricula"] = st.text_input("Matrícula", key=f"mat_{ks}")
            respostas["Semestre"] = st.selectbox("Semestre Atual", [f"{i}º Semestre" for i in range(1, 11)], key=f"sem_{ks}")
            respostas["Curriculo"] = st.radio("Matriz Curricular", ["Novo (2023.1)", "Antigo (2005.1)"], key=f"curr_{ks}")
            respostas["Data_Registro"] = obter_hora_ceara()
            
            st.success("✅ Auto-Save Ativo")

        with tab_ajuda:
            st.markdown("### 📘 MANUAL DE TRANSCRIÇÃO")
            
            st.markdown('<div class="manual-box">', unsafe_allow_html=True)
            st.markdown("**1. CONDUTA GERAL**")
            st.caption("A fidelidade aos dados é prioridade. Não altere ou interprete as respostas. Transcreva exatamente o que vê.")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="manual-box">', unsafe_allow_html=True)
            st.markdown("**2. ESCALA E 'N/A'**")
            st.markdown("""
            * **N/A (Não se Aplica):** Use para campos em branco, rasurados ou ilegíveis. (Não zera a média).
            * **0 a 5:** Transcreva a marcação exata.
            * **Dupla marcação?** Anule a questão usando **N/A**.
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="manual-box">', unsafe_allow_html=True)
            st.markdown("**3. REGRAS DE TEXTO**")
            st.markdown("""
            * **Ilegível?** Digite `[Ilegível]`.
            * **Seção Final Vazia?** Digite `EM BRANCO` ou `NÃO RESPONDEU`.
            * **Erros de português?** Mantenha-os (fidelidade).
            """)
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# LÓGICA 1: NOVA TRANSCRIÇÃO (WIZARD)
# ==============================================================================
if modo_operacao == "📝 Nova Transcrição":
    # Navegação Superior
    secao_ativa = st.radio("Etapas:", SECOES, horizontal=True, key="navegacao_atual", label_visibility="collapsed")
    st.markdown("---")
    
    k_suffix = f"_{st.session_state.form_key}" # Sufixo para garantir unicidade dos widgets

    # --- SEÇÃO 1 ---
    if secao_ativa == SECOES[0]:
        st.markdown("### 1. COMPETÊNCIAS TÉCNICAS E GERAIS")
        renderizar_pergunta("1. Projetar e conduzir experimentos e interpretar resultados", "q1", key_suffix=k_suffix)
        renderizar_pergunta("2. Desenvolver e/ou utilizar novas ferramentas e técnicas", "q2", key_suffix=k_suffix)
        renderizar_pergunta("3. Conceber, projetar e analisar sistemas, produtos e processos", "q3", key_suffix=k_suffix)
        renderizar_pergunta("4. Formular, conceber e avaliar soluções para problemas de engenharia", "q4", key_suffix=k_suffix)
        renderizar_pergunta("5. Analisar e compreender fenômenos físicos e químicos através de modelos", "q5", key_suffix=k_suffix)
        renderizar_pergunta("6. Comunicar-se nas formas escrita, oral e gráfica", "q6", key_suffix=k_suffix)
        renderizar_pergunta("7. Trabalhar e liderar equipes profissionais e multidisciplinares", "q7", key_suffix=k_suffix)
        renderizar_pergunta("8. Aplicar ética e legislação no exercício profissional", "q8", key_suffix=k_suffix)
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_1")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SEÇÃO 2 ---
    elif secao_ativa == SECOES[1]:
        st.markdown("### 2. COMPETÊNCIAS ESPECÍFICAS")
        renderizar_pergunta("9. Aplicar conhecimentos matemáticos, científicos e tecnológicos", "q9", key_suffix=k_suffix)
        renderizar_pergunta("10. Compreender e modelar transferência de quantidade de movimento, calor e massa", "q10", key_suffix=k_suffix)
        renderizar_pergunta("11. Aplicar conhecimentos de fenômenos de transporte ao projeto", "q11", key_suffix=k_suffix)
        renderizar_pergunta("12. Compreender mecanismos de transformação da matéria e energia", "q12", key_suffix=k_suffix)
        renderizar_pergunta("13. Projetar sistemas de recuperação, separação e purificação", "q13", key_suffix=k_suffix)
        renderizar_pergunta("14. Compreender mecanismos cinéticos de reações químicas", "q14", key_suffix=k_suffix)
        renderizar_pergunta("15. Projetar e otimizar sistemas reacionais e reatores", "q15", key_suffix=k_suffix)
        renderizar_pergunta("16. Projetar sistemas de controle de processos industriais", "q16", key_suffix=k_suffix)
        renderizar_pergunta("17. Projetar e otimizar plantas industriais (ambiental/segurança)", "q17", key_suffix=k_suffix)
        st.markdown("#### Eixos de Formação Prática")
        renderizar_pergunta("18. Aplicação de conhecimentos em projeto básico e dimensionamento", "q18", key_suffix=k_suffix)
        renderizar_pergunta("19. Execução de projetos de produção e melhorias de processos", "q19", key_suffix=k_suffix)
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_2")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SEÇÃO 3 ---
    elif secao_ativa == SECOES[2]:
        st.markdown("### 3. DISCIPLINAS BÁSICAS")
        with st.expander("CÁLCULO DIFERENCIAL E INTEGRAL", expanded=True):
            renderizar_pergunta("21. Analisar grandes volumes de dados", "calc_21", key_suffix=k_suffix)
            renderizar_pergunta("52. Formação Básica", "calc_52", key_suffix=k_suffix)
        with st.expander("FÍSICA GERAL", expanded=True):
            renderizar_pergunta("22. Analisar criticamente a operação e manutenção de sistemas", "fis_22", key_suffix=k_suffix)
            renderizar_pergunta("53. Ciência da Engenharia", "fis_53", key_suffix=k_suffix)
        with st.expander("QUÍMICA GERAL E ANALÍTICA", expanded=True):
            renderizar_pergunta("23. Aplicar conhecimentos de transformação a processos", "qui_23", key_suffix=k_suffix)
            renderizar_pergunta("24. Conceber e desenvolver produtos e processos", "qui_24", key_suffix=k_suffix)
        with st.expander("TERMODINÂMICA", expanded=True):
            renderizar_pergunta("25. Projetar sistemas de suprimento energético", "termo_25", key_suffix=k_suffix)
            renderizar_pergunta("54. Ciência da Eng. Química", "termo_54", key_suffix=k_suffix)
        with st.expander("FENÔMENOS DE TRANSPORTE E MECÂNICA DOS FLUIDOS", expanded=True):
            renderizar_pergunta("26. Aplicar conhecimentos de fenômenos de transporte", "ft_26", key_suffix=k_suffix)
            renderizar_pergunta("27. Comunicar-se tecnicamente e usar recursos gráficos", "ft_27", key_suffix=k_suffix)
            renderizar_pergunta("28. Implantar, implementar e controlar soluções", "mecflu_28", key_suffix=k_suffix)
            renderizar_pergunta("29. Operar e supervisionar instalações", "mecflu_29", key_suffix=k_suffix)
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_3")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SEÇÃO 4 ---
    elif secao_ativa == SECOES[3]:
        st.markdown("### 4. DISCIPLINAS PROFISSIONALIZANTES")
        with st.expander("OPERAÇÕES UNITÁRIAS (I e II)", expanded=True):
            renderizar_pergunta("30. Inspecionar e coordenar manutenção", "op1_30", key_suffix=k_suffix)
            renderizar_pergunta("55. Tecnologia Industrial", "op1_55", key_suffix=k_suffix)
            renderizar_pergunta("31. Elaborar estudos de impactos ambientais", "op2_31", key_suffix=k_suffix)
            renderizar_pergunta("32. Projetar processos de tratamento ambiental", "op2_32", key_suffix=k_suffix)
        with st.expander("REATORES QUÍMICOS", expanded=True):
            renderizar_pergunta("33. Gerir recursos estratégicos na produção", "reat_33", key_suffix=k_suffix)
            renderizar_pergunta("34. Aplicar modelos de produção e controle de qualidade", "reat_34", key_suffix=k_suffix)
        with st.expander("CONTROLE DE PROCESSOS E PROJETOS", expanded=True):
            renderizar_pergunta("35. Controle e supervisão de instalações", "ctrl_35", key_suffix=k_suffix)
            renderizar_pergunta("36. Gestão de empreendimentos industriais", "ctrl_36", key_suffix=k_suffix)
            renderizar_pergunta("56. Projetos Industriais e Gestão", "proj_56", key_suffix=k_suffix)
            renderizar_pergunta("57. Ética, Meio Ambiente e Humanidades", "proj_57", key_suffix=k_suffix)
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_4")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SEÇÃO 5 ---
    elif secao_ativa == SECOES[4]:
        st.markdown("### 5. DISCIPLINAS AVANÇADAS E COMPLEMENTARES")
        with st.expander("GESTÃO, ECONOMIA E MEIO AMBIENTE", expanded=True):
            renderizar_pergunta("37. Eng. Econômica: Aprender novos conceitos", "econ_37", key_suffix=k_suffix)
            renderizar_pergunta("38. Eng. Econômica: Visão global", "econ_38", key_suffix=k_suffix)
            renderizar_pergunta("39. Gestão da Produção: Comprometimento", "gest_39", key_suffix=k_suffix)
            renderizar_pergunta("40. Gestão da Produção: Resultados", "gest_40", key_suffix=k_suffix)
            renderizar_pergunta("41. Eng. Ambiental: Inovação", "amb_41", key_suffix=k_suffix)
            renderizar_pergunta("42. Eng. Ambiental: Novas situações", "amb_42", key_suffix=k_suffix)
            renderizar_pergunta("43. Segurança: Lidar com incertezas", "seg_43", key_suffix=k_suffix)
            renderizar_pergunta("44. Segurança: Iniciativa e decisão", "seg_44", key_suffix=k_suffix)
        with st.expander("ATIVIDADES PRÁTICAS (LABORATÓRIO E ESTÁGIO)", expanded=True):
            renderizar_pergunta("45. Laboratório: Criatividade", "lab_45", key_suffix=k_suffix)
            renderizar_pergunta("46. Laboratório: Relacionamento", "lab_46", key_suffix=k_suffix)
            renderizar_pergunta("47. Estágio: Autocontrole emocional", "est_47", key_suffix=k_suffix)
            renderizar_pergunta("48. Estágio: Capacidade empreendedora", "est_48", key_suffix=k_suffix)
        with st.expander("DISCIPLINAS OPTATIVAS E INTEGRADORAS", expanded=True):
            renderizar_pergunta("49. Biotecnologia: Analisar grandes volumes de dados", "bio_49", key_suffix=k_suffix)
            renderizar_pergunta("50. Biotecnologia: Novas ferramentas", "bio_50", key_suffix=k_suffix)
            renderizar_pergunta("51. Petróleo e Gás: Projetar recuperação", "petro_51", key_suffix=k_suffix)
            renderizar_pergunta("52. Petróleo e Gás: Projetar reatores", "petro_52", key_suffix=k_suffix)
            renderizar_pergunta("57. Simulação: Analisar dados", "sim_57", key_suffix=k_suffix)
            renderizar_pergunta("58. Simulação: Comunicação técnica", "sim_58", key_suffix=k_suffix)
            renderizar_pergunta("59. Otimização: Soluções", "otim_59", key_suffix=k_suffix)
            renderizar_pergunta("60. Otimização: Modelos", "otim_60", key_suffix=k_suffix)
            renderizar_pergunta("61. TCC: Comunicação", "tcc_61", key_suffix=k_suffix)
            renderizar_pergunta("62. TCC: Liderança", "tcc_62", key_suffix=k_suffix)
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_5")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SEÇÃO 6: REFLEXÃO FINAL (OBRIGATÓRIA) ---
    elif secao_ativa == SECOES[5]:
        st.markdown("### 6. REFLEXÃO FINAL E AUTOAVALIAÇÃO")
        st.warning("⚠️ **ATENÇÃO:** Preenchimento OBRIGATÓRIO. Se o formulário físico estiver vazio, digite 'EM BRANCO'.")
        
        renderizar_pergunta("20. Capacidade de aprender rapidamente novos conceitos (Geral)", "q20_indiv", key_suffix=k_suffix)
        
        st.markdown("#### TRANSCRIÇÃO DAS RESPOSTAS ABERTAS")
        
        txt_fortes = st.text_area("Pontos Fortes (Obrigatório)", key=f"fortes_{k_suffix}")
        txt_fracos = st.text_area("Pontos a Desenvolver (Obrigatório)", key=f"fracos_{k_suffix}")
        txt_prat = st.text_area("Contribuição das atividades", key=f"prat_{k_suffix}")
        txt_ex = st.text_area("Exemplos de aplicação", key=f"ex_{k_suffix}")
        txt_fut1 = st.text_area("Competências futuras", key=f"fut1_{k_suffix}")
        txt_fut2 = st.text_area("Plano de desenvolvimento", key=f"fut2_{k_suffix}")
        txt_obs = st.text_area("Comentários Finais", key=f"obsf_{k_suffix}")

        st.markdown("---")
        st.markdown('<div class="botao-final">', unsafe_allow_html=True)
        if st.button("💾 FINALIZAR E SALVAR REGISTRO", type="primary"):
            
            # --- CONSOLIDAÇÃO DOS DADOS DO SESSION_STATE ---
            dados_salvar = {
                "Petiano_Responsavel": respostas["Petiano_Responsavel"],
                "Nome": respostas["Nome"],
                "Matricula": respostas["Matricula"],
                "Semestre": respostas["Semestre"],
                "Curriculo": respostas["Curriculo"],
                "Data_Registro": respostas["Data_Registro"],
                # Textos
                "Autoavaliação: Pontos Fortes": txt_fortes,
                "Autoavaliação: Pontos a Desenvolver": txt_fracos,
                "Contribuição Prática": txt_prat,
                "Exemplos de Aplicação": txt_ex,
                "Competências Futuras": txt_fut1,
                "Plano de Desenvolvimento": txt_fut2,
                "Observações Finais": txt_obs
            }
            
            # Varre o session state para pegar notas e obs dinâmicas
            for k, v in st.session_state.items():
                if k.startswith(f"nota_") and k.endswith(f"_{k_suffix}"):
                    clean_key = k.replace("nota_", "").replace(f"_{k_suffix}", "")
                    dados_salvar[clean_key] = v
                elif k.startswith(f"obs_") and k.endswith(f"_{k_suffix}"):
                    clean_key = k.replace("obs_", "Obs_").replace(f"_{k_suffix}", "")
                    dados_salvar[clean_key] = v

            # VALIDAÇÃO DE OBRIGATORIEDADE
            erros = []
            if not dados_salvar["Nome"]: erros.append("Nome do Discente")
            if not dados_salvar["Petiano_Responsavel"]: erros.append("Responsável")
            if not dados_salvar["Autoavaliação: Pontos Fortes"] or not dados_salvar["Autoavaliação: Pontos a Desenvolver"]:
                erros.append("Campos de Reflexão Final (Digite 'EM BRANCO' se vazio)")

            if erros:
                st.error(f"❌ AÇÃO BLOQUEADA. Preencha: {', '.join(erros)}")
            else:
                try:
                    df_new = pd.DataFrame([dados_salvar])
                    if os.path.exists(ARQUIVO_DB):
                        df_new.to_csv(ARQUIVO_DB, mode='a', header=False, index=False)
                    else:
                        df_new.to_csv(ARQUIVO_DB, mode='w', header=True, index=False)
                    
                    st.balloons()
                    st.success(f"✅ Transcrição de {dados_salvar['Nome']} salva com sucesso!")
                    limpar_formulario()
                    st.rerun()
                except PermissionError:
                    st.error("❌ ERRO: O arquivo Excel está aberto. Feche-o e tente novamente.")
                except Exception as e:
                    st.error(f"❌ ERRO INESPERADO: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-Save do Rascunho
    auto_save()

# ==============================================================================
# LÓGICA 2: EDIÇÃO DE REGISTROS
# ==============================================================================
elif modo_operacao == "✏️ Editar Registro":
    st.markdown("### ✏️ MODO DE EDIÇÃO")
    if not os.path.exists(ARQUIVO_DB):
        st.warning("Banco de dados vazio.")
    else:
        try:
            df = pd.read_csv(ARQUIVO_DB, dtype=str)
            opcoes_alunos = df.apply(lambda x: f"{x.name} | {x['Nome']} ({x['Matricula']})", axis=1)
            aluno_sel = st.selectbox("Selecione o registro:", opcoes_alunos)
            idx = int(aluno_sel.split(" | ")[0])
            dados_aluno = df.iloc[idx]
            
            with st.form("editor"):
                st.subheader("Dados Cadastrais")
                c1, c2 = st.columns(2)
                novo_nome = c1.text_input("Nome", value=dados_aluno["Nome"])
                nova_mat = c2.text_input("Matrícula", value=dados_aluno["Matricula"])
                
                st.subheader("Edição de Notas (Amostra)")
                st.info("Para editar notas específicas, localize a coluna abaixo.")
                
                # Exemplo de edição para Q1 e Q2 (Expandir se necessário)
                # Criar um dicionário de mudanças
                novas_notas = {}
                
                # Loop por colunas de nota encontradas no DF
                cols_notas = [c for c in df.columns if c not in ['Nome', 'Matricula'] and not c.startswith("Obs") and not c.startswith("Auto") and not c.startswith("Petiano")]
                
                col_sel_edit = st.selectbox("Escolha a competência para ajustar:", cols_notas)
                val_atual = dados_aluno[col_sel_edit] if col_sel_edit in dados_aluno else "N/A"
                if val_atual not in ["N/A", "0", "1", "2", "3", "4", "5"]: val_atual = "N/A"
                
                novo_valor = st.select_slider(f"Ajustar nota de: {col_sel_edit}", options=["N/A", "0", "1", "2", "3", "4", "5"], value=val_atual)
                
                if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                    df.at[idx, "Nome"] = novo_nome
                    df.at[idx, "Matricula"] = nova_mat
                    df.at[idx, col_sel_edit] = novo_valor
                    df.to_csv(ARQUIVO_DB, index=False)
                    st.success("Registro atualizado!")
                    st.rerun()
        except: st.error("Erro ao carregar dados.")

# ==============================================================================
# LÓGICA 3: PAINEL GERENCIAL
# ==============================================================================
elif modo_operacao == "📊 Painel Gerencial":
    st.markdown("### 📊 INDICADORES DE DESEMPENHO")
    if os.path.exists(ARQUIVO_DB):
        try:
            df = pd.read_csv(ARQUIVO_DB, dtype={'Matricula': str})
            
            # Filtro por Petiano
            filtro_pet = st.selectbox("Filtrar por Responsável:", ["Todos"] + sorted(list(df['Petiano_Responsavel'].unique())))
            if filtro_pet != "Todos": df = df[df['Petiano_Responsavel'] == filtro_pet]
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Formulários", len(df))
            
            # Filtra colunas numéricas (Ignorando N/A e textos)
            cols_ignorar = ['Nome', 'Matricula', 'Semestre', 'Curriculo', 'Data_Registro', 'Petiano_Responsavel']
            cols_calc = [c for c in df.columns if c not in cols_ignorar and not c.startswith("Obs") and not c.startswith("Auto") and not c.startswith("Contribuição") and not c.startswith("Exemplos") and not c.startswith("Competências") and not c.startswith("Plano") and not c.startswith("Comentários") and not c.startswith("Justificativa")]
            
            df_numeric = df[cols_calc].apply(pd.to_numeric, errors='coerce')
            
            if not df_numeric.empty:
                media = df_numeric.mean().mean()
                c2.metric("Média Geral (Exclui N/A)", f"{media:.2f}/5.0")
            
            if 'Data_Registro' in df.columns:
                last = pd.to_datetime(df['Data_Registro']).max()
                c3.metric("Última Atividade", last.strftime("%d/%m %H:%M"))
            
            st.markdown("#### Detalhamento")
            st.dataframe(df, use_container_width=True, height=500)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Relatório (Excel)", csv, "sac_relatorio.csv", "text/csv")
        except Exception as e: st.error(f"Erro: {e}")
    else: st.info("Sem dados.")
