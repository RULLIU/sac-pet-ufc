import streamlit as st
import pandas as pd
import plotly.express as px
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
# 2. ESTILO VISUAL (INSTITUCIONAL & RESPONSIVO)
# ==============================================================================
st.markdown("""
    <style>
    /* VARIÁVEIS GERAIS */
    :root { --primary-color: #002060; }
    .stApp { font-family: 'Segoe UI', 'Roboto', sans-serif; }
    
    /* TÍTULOS */
    h1, h2, h3, h4 {
        color: var(--primary-color) !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* MODO ESCURO */
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, h4 { color: #82b1ff !important; }
        .pergunta-card { background-color: #1e1e1e !important; border-left: 5px solid #82b1ff !important; border: 1px solid #333 !important; }
        .manual-box { background-color: #262730 !important; border: 1px solid #444 !important; }
        .edit-warning { background-color: #3e2723 !important; color: #ffcc80 !important; border: 1px solid #ffab91 !important; }
    }

    /* MODO CLARO */
    @media (prefers-color-scheme: light) {
        .stApp { background-color: #ffffff !important; }
        .pergunta-card { background-color: #fcfcfc !important; border-left: 5px solid #002060 !important; border: 1px solid #e0e0e0 !important; }
        .manual-box { background-color: #f0f2f6 !important; border: 1px solid #ddd !important; }
        .edit-warning { background-color: #fff3e0 !important; color: #e65100 !important; border: 1px solid #ffe0b2 !important; }
    }

    /* CARD DA PERGUNTA */
    .pergunta-card {
        border-radius: 8px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .pergunta-texto {
        font-size: 1.1rem; font-weight: 700; margin-bottom: 15px; opacity: 0.95;
    }

    /* BOTÕES */
    .stButton button {
        border-radius: 6px; font-weight: 700; text-transform: uppercase; height: 3.5em; width: 100%; transition: all 0.3s ease;
    }
    /* Botão "Próximo" */
    .botao-avancar button {
        background-color: transparent; border: 2px solid #002060; color: #002060;
    }
    .botao-avancar button:hover {
        background-color: #002060; color: white; transform: translateX(5px);
    }
    /* Botão "Finalizar" */
    .botao-final button {
        background-color: #002060 !important; color: white !important; border: none; height: 4.5em; font-size: 1.1rem;
    }
    .botao-final button:hover {
        background-color: #003399 !important; transform: scale(1.02);
    }

    /* CAIXAS DE MENSAGEM */
    .manual-box { padding: 15px; border-radius: 8px; margin-bottom: 15px; }
    .edit-warning { padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold; }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
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
# 4. FUNÇÕES DE SUPORTE E LISTAS GLOBAIS
# ==============================================================================
SECOES = [
    "1. Gerais", "2. Específicas", "3. Básicas", 
    "4. Profissionais", "5. Avançadas", "6. Reflexão"
]

# Listas globais
LISTA_PETIANOS = sorted([
    "", "Ana Carolina", "Ana Clara", "Ana Júlia", 
    "Eric Rullian", "Gildelandio Junior", 
    "Lucas Mossmann (trainee)", "Pedro Paulo"
])
LISTA_SEMESTRES = [f"{i}º Semestre" for i in range(1, 11)]
LISTA_CURRICULOS = ["Novo (2023.1)", "Antigo (2005.1)", "Troca de Matriz (Velha -> Nova)"]

if 'form_key' not in st.session_state: st.session_state.form_key = 0
if 'navegacao_atual' not in st.session_state: st.session_state.navegacao_atual = SECOES[0]

def carregar_backup():
    if os.path.exists(ARQUIVO_BACKUP):
        try:
            with open(ARQUIVO_BACKUP, "r", encoding='utf-8') as f:
                dados = json.load(f)
                for k, v in dados.items():
                    if k.endswith(f"_{st.session_state.form_key}"):
                        st.session_state[k] = v
        except: pass

if 'backup_restaurado' not in st.session_state:
    carregar_backup()
    st.session_state.backup_restaurado = True

def salvar_estado():
    try:
        dados_salvar = {k: v for k, v in st.session_state.items() if (k.startswith("nota_") or k.startswith("obs_") or k.startswith("ident_")) and isinstance(v, (str, int, float, bool))}
        with open(ARQUIVO_BACKUP, "w", encoding='utf-8') as f:
            json.dump(dados_salvar, f, indent=4, ensure_ascii=False)
    except: pass

def navegar_proxima():
    try:
        idx = SECOES.index(st.session_state.navegacao_atual)
        if idx < len(SECOES) - 1:
            st.session_state.navegacao_atual = SECOES[idx + 1]
            salvar_estado()
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
    Renderiza o bloco de pergunta.
    """
    k = key_suffix if key_suffix else f"_{st.session_state.form_key}"
    
    with st.container():
        st.markdown(f"""<div class="pergunta-card"><div class="pergunta-texto">{texto_pergunta}</div></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            val = st.select_slider(
                "Nível de Competência", 
                options=["N/A", "0", "1", "2", "3", "4", "5"], 
                value=str(valor_padrao), 
                key=f"nota_{id_unica}{k}",
                help="Selecione 'N/A' se vazio."
            )
        with c2:
            obs = st.text_input(
                "Transcrição de Obs.", 
                value=str(obs_padrao) if pd.notna(obs_padrao) else "",
                placeholder="Comentários...", 
                key=f"obs_{id_unica}{k}"
            )
    return val, obs

# ==============================================================================
# 5. BARRA LATERAL (MENU PRINCIPAL)
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
        tab_id, tab_manual = st.tabs(["👤 Identificação", "📘 Manual"])
        
        with tab_id:
            st.info("Preencha conforme o papel.")
            k_sfx = f"_{st.session_state.form_key}"
            
            respostas["Petiano_Responsavel"] = st.selectbox("Responsável", LISTA_PETIANOS, key=f"ident_pet{k_sfx}")
            respostas["Nome"] = st.text_input("Nome do Discente", key=f"ident_nome{k_sfx}")
            respostas["Matricula"] = st.text_input("Matrícula", key=f"ident_mat{k_sfx}")
            respostas["Semestre"] = st.selectbox("Semestre", LISTA_SEMESTRES, key=f"ident_sem{k_sfx}")
            respostas["Curriculo"] = st.radio("Matriz", LISTA_CURRICULOS, key=f"ident_curr{k_sfx}")
            
            if st.button("🗑️ Limpar Formulário"):
                limpar_formulario()
                st.rerun()

        with tab_manual:
            st.markdown("### 📘 PROCEDIMENTOS PADRÃO")
            
            with st.expander("1. Preparação e Conduta", expanded=True):
                st.caption("A fidelidade aos dados é a prioridade absoluta.")
                st.markdown("""
                * **Não altere erros:** Transcreva exatamente o que vê (ipsis litteris).
                * **Letra Ilegível:** Digite `[ILEGÍVEL]`.
                """)

            with st.expander("2. Escala Numérica e 'N/A'"):
                st.markdown("""
                * **N/A (Não se Aplica):** Use OBRIGATORIAMENTE quando:
                    * O campo está em branco.
                    * Há rasura que impede identificar a nota.
                    * O aluno marcou duas opções.
                * **Nota:** N/A não conta na média.
                """)

            with st.expander("3. Seção Final (Obrigatória)"):
                st.error("""
                O sistema **BLOQUEIA** o salvamento se a Reflexão Final estiver vazia.
                Se o aluno não escreveu, digite **EM BRANCO** ou **NÃO RESPONDEU**.
                """)

# ==============================================================================
# LÓGICA 1: WIZARD DE TRANSCRIÇÃO (NOVA)
# ==============================================================================
if modo_operacao == "📝 Nova Transcrição":
    secao_ativa = st.radio("Etapas:", SECOES, horizontal=True, key="navegacao_atual", label_visibility="collapsed")
    st.markdown("---")
    
    k_suffix = f"_{st.session_state.form_key}"

    # --- SEÇÃO 1: GERAIS ---
    if secao_ativa == SECOES[0]:
        st.markdown("### 1. COMPETÊNCIAS TÉCNICAS E GERAIS")
        renderizar_pergunta("1. Projetar e conduzir experimentos e interpretar resultados", "q1", key_suffix=k_suffix)
        renderizar_pergunta("2. Desenvolver e/ou utilizar novas ferramentas e técnicas", "q2", key_suffix=k_suffix)
        renderizar_pergunta("3. Conceber, projetar e analisar sistemas, produtos e processos", "q3", key_suffix=k_suffix)
        renderizar_pergunta("4. Formular, conceber e avaliar soluções para problemas de engenharia", "q4", key_suffix=k_suffix)
        renderizar_pergunta("5. Analisar e compreender fenômenos físicos e químicos através de modelos", "q5", key_suffix=k_suffix)
        renderizar_pergunta("6. Comunicação técnica", "q6", key_suffix=k_suffix)
        renderizar_pergunta("7. Trabalhar e liderar equipes profissionais", "q7", key_suffix=k_suffix)
        renderizar_pergunta("8. Aplicar ética e legislação no exercício profissional", "q8", key_suffix=k_suffix)
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav1")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SEÇÃO 2: ESPECÍFICAS ---
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
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav2")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SEÇÃO 3: BÁSICAS ---
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
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav3")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SEÇÃO 4: PROFISSIONAIS ---
    elif secao_ativa == SECOES[3]:
        st.markdown("### 4. DISCIPLINAS PROFISSIONALIZANTES")
        with st.expander("OPERAÇÕES UNITÁRIAS (I e II)", expanded=True):
            renderizar_pergunta("30. Inspecionar manutenção", "op1_30", key_suffix=k_suffix)
            renderizar_pergunta("55. Tecnologia Industrial", "op1_55", key_suffix=k_suffix)
            renderizar_pergunta("31. Elaborar estudos ambientais", "op2_31", key_suffix=k_suffix)
            renderizar_pergunta("32. Projetar tratamento ambiental", "op2_32", key_suffix=k_suffix)
        with st.expander("REATORES QUÍMICOS", expanded=True):
            renderizar_pergunta("33. Gerir recursos", "reat_33", key_suffix=k_suffix)
            renderizar_pergunta("34. Controle de qualidade", "reat_34", key_suffix=k_suffix)
        with st.expander("CONTROLE DE PROCESSOS E PROJETOS", expanded=True):
            renderizar_pergunta("35. Controle: Supervisão", "ctrl_35", key_suffix=k_suffix)
            renderizar_pergunta("36. Gestão de empreendimentos", "ctrl_36", key_suffix=k_suffix)
            renderizar_pergunta("56. Gestão Industrial", "proj_56", key_suffix=k_suffix)
            renderizar_pergunta("57. Ética e Humanidades", "proj_57", key_suffix=k_suffix)
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav4")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SEÇÃO 5: AVANÇADAS ---
    elif secao_ativa == SECOES[4]:
        st.markdown("### 5. DISCIPLINAS AVANÇADAS")
        with st.expander("GESTÃO, ECONOMIA E MEIO AMBIENTE", expanded=True):
            renderizar_pergunta("37. Eng. Econômica: Novos conceitos", "econ_37", key_suffix=k_suffix)
            renderizar_pergunta("38. Eng. Econômica: Visão global", "econ_38", key_suffix=k_suffix)
            renderizar_pergunta("39. Gestão Produção: Comprometimento", "gest_39", key_suffix=k_suffix)
            renderizar_pergunta("40. Gestão Produção: Resultados", "gest_40", key_suffix=k_suffix)
            renderizar_pergunta("41. Eng. Ambiental: Inovação", "amb_41", key_suffix=k_suffix)
            renderizar_pergunta("42. Eng. Ambiental: Novas situações", "amb_42", key_suffix=k_suffix)
            renderizar_pergunta("43. Segurança: Incertezas", "seg_43", key_suffix=k_suffix)
            renderizar_pergunta("44. Segurança: Decisão", "seg_44", key_suffix=k_suffix)
        with st.expander("ATIVIDADES PRÁTICAS (LABORATÓRIO E ESTÁGIO)", expanded=True):
            renderizar_pergunta("45. Laboratório: Criatividade", "lab_45", key_suffix=k_suffix)
            renderizar_pergunta("46. Laboratório: Relacionamento", "lab_46", key_suffix=k_suffix)
            renderizar_pergunta("47. Estágio: Autocontrole emocional", "est_47", key_suffix=k_suffix)
            renderizar_pergunta("48. Estágio: Capacidade empreendedora", "est_48", key_suffix=k_suffix)
        with st.expander("DISCIPLINAS OPTATIVAS E INTEGRADORAS", expanded=True):
            renderizar_pergunta("49. Biotec: Dados", "bio_49", key_suffix=k_suffix)
            renderizar_pergunta("50. Biotec: Ferramentas", "bio_50", key_suffix=k_suffix)
            renderizar_pergunta("51. Petróleo: Recuperação", "petro_51", key_suffix=k_suffix)
            renderizar_pergunta("52. Petróleo: Reatores", "petro_52", key_suffix=k_suffix)
            renderizar_pergunta("53. Polímeros: Cinética", "poli_53", key_suffix=k_suffix)
            renderizar_pergunta("54. Polímeros: Produtos", "poli_54", key_suffix=k_suffix)
            renderizar_pergunta("55. Catálise: Mecanismos de transformação", "cat_55", key_suffix=k_suffix)
            renderizar_pergunta("56. Catálise: Aplicar na produção", "cat_56", key_suffix=k_suffix)
            renderizar_pergunta("57. Simulação: Dados", "sim_57", key_suffix=k_suffix)
            renderizar_pergunta("58. Simulação: Comunicação", "sim_58", key_suffix=k_suffix)
            renderizar_pergunta("59. Otimização: Soluções", "otim_59", key_suffix=k_suffix)
            renderizar_pergunta("60. Otimização: Modelos", "otim_60", key_suffix=k_suffix)
            renderizar_pergunta("61. TCC: Comunicação", "tcc_61", key_suffix=k_suffix)
            renderizar_pergunta("62. TCC: Liderança", "tcc_62", key_suffix=k_suffix)
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav5")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SEÇÃO 6: REFLEXÃO FINAL ---
    elif secao_ativa == SECOES[5]:
        st.markdown("### 6. REFLEXÃO FINAL E AUTOAVALIAÇÃO")
        st.warning("⚠️ **ATENÇÃO:** Preenchimento OBRIGATÓRIO. Se o formulário físico estiver vazio, digite 'EM BRANCO'.")
        
        renderizar_pergunta("20. Capacidade de aprender rapidamente novos conceitos (Geral)", "q20_indiv", key_suffix=k_suffix)
        
        st.markdown("#### TRANSCRIÇÃO DAS RESPOSTAS ABERTAS")
        
        txt_fortes = st.text_area("Pontos Fortes (Obrigatório)", key=f"obs_fortes{k_suffix}")
        txt_fracos = st.text_area("Pontos a Desenvolver (Obrigatório)", key=f"obs_fracos{k_suffix}")
        txt_prat = st.text_area("Contribuição Prática", key=f"obs_prat{k_suffix}")
        txt_ex = st.text_area("Exemplos de Aplicação", key=f"obs_ex{k_suffix}")
        txt_fut1 = st.text_area("Competências Futuras", key=f"obs_fut1{k_suffix}")
        txt_fut2 = st.text_area("Plano de Desenvolvimento", key=f"obs_fut2{k_suffix}")
        txt_final = st.text_area("Comentários Finais", key=f"obs_final{k_suffix}")

        st.markdown("---")
        st.markdown('<div class="botao-final">', unsafe_allow_html=True)
        if st.button("💾 FINALIZAR E SALVAR REGISTRO", type="primary"):
            
            # --- CONSOLIDAÇÃO DOS DADOS ---
            dados_salvar = {
                "Petiano_Responsavel": st.session_state.get(f"ident_pet{k_suffix}", ""),
                "Nome": st.session_state.get(f"ident_nome{k_suffix}", ""),
                "Matricula": st.session_state.get(f"ident_mat{k_suffix}", ""),
                "Semestre": st.session_state.get(f"ident_sem{k_suffix}", ""),
                "Curriculo": st.session_state.get(f"ident_curr{k_suffix}", ""),
                "Data_Registro": obter_hora_ceara(),
                "Autoavaliação: Pontos Fortes": txt_fortes,
                "Autoavaliação: Pontos a Desenvolver": txt_fracos,
                "Contribuição Prática": txt_prat,
                "Exemplos de Aplicação": txt_ex,
                "Competências Futuras": txt_fut1,
                "Plano de Desenvolvimento": txt_fut2,
                "Observações Finais": txt_final
            }
            
            # Perguntas Dinâmicas
            for k, v in st.session_state.items():
                if k.endswith(k_suffix):
                    if k.startswith("nota_"):
                        col_name = k.replace("nota_", "").replace(k_suffix, "")
                        dados_salvar[col_name] = v
                    elif k.startswith("obs_") and "fortes" not in k and "fracos" not in k:
                        col_name = "Obs_" + k.replace("obs_", "").replace(k_suffix, "")
                        dados_salvar[col_name] = v

            # VALIDAÇÃO
            erros = []
            if not dados_salvar["Nome"]: erros.append("Nome do Discente")
            if not dados_salvar["Petiano_Responsavel"]: erros.append("Petiano Responsável")
            if not dados_salvar["Autoavaliação: Pontos Fortes"] or not dados_salvar["Autoavaliação: Pontos a Desenvolver"]:
                erros.append("Campos de Reflexão Final")

            if erros:
                st.error(f"❌ IMPOSSÍVEL SALVAR: {', '.join(erros)}")
            else:
                try:
                    df_new = pd.DataFrame([dados_salvar])
                    if os.path.exists(ARQUIVO_DB):
                        # --- CORREÇÃO DE SEGURANÇA PARA ARQUIVOS ANTIGOS ---
                        try:
                            df_antigo = pd.read_csv(ARQUIVO_DB, dtype=str)
                            if 'Data_Registro' not in df_antigo.columns:
                                df_antigo['Data_Registro'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            df_final = pd.concat([df_antigo, df_new], ignore_index=True)
                            df_final.to_csv(ARQUIVO_DB, index=False)
                        except:
                            df_new.to_csv(ARQUIVO_DB, mode='w', header=True, index=False)
                    else:
                        df_new.to_csv(ARQUIVO_DB, mode='w', header=True, index=False)
                    
                    st.balloons()
                    st.success(f"✅ Transcrição de {dados_salvar['Nome']} salva com sucesso!")
                    limpar_formulario()
                    st.rerun()
                except PermissionError:
                    st.error("❌ ERRO: Feche o arquivo Excel aberto.")
                except Exception as e:
                    st.error(f"❌ ERRO: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    salvar_estado()

# ==============================================================================
# LÓGICA 2: MODO DE EDIÇÃO (CORRIGIDO E COMPLETO)
# ==============================================================================
elif modo_operacao == "✏️ Editar Registro":
    st.markdown("### ✏️ MODO DE EDIÇÃO")
    st.markdown("<div class='edit-warning'>⚠️ Atenção: As alterações feitas aqui sobrescrevem permanentemente o registro original.</div>", unsafe_allow_html=True)
    
    if not os.path.exists(ARQUIVO_DB):
        st.warning("Banco de dados vazio.")
    else:
        try:
            df = pd.read_csv(ARQUIVO_DB, dtype=str)
            if df.empty: st.warning("Nenhum dado.")
            else:
                opcoes = df.apply(lambda x: f"{x.name} | {x['Nome']} ({x['Matricula']})", axis=1)
                sel = st.selectbox("Selecione o registro para corrigir:", opcoes)
                idx = int(sel.split(" | ")[0])
                dados = df.iloc[idx]
                
                with st.form("form_edicao_completa"):
                    st.subheader("1. Dados Cadastrais")
                    c1, c2 = st.columns(2)
                    
                    new_nome = c1.text_input("Nome", value=dados.get("Nome", ""))
                    new_mat = c2.text_input("Matrícula", value=dados.get("Matricula", ""))
                    
                    # Logica de Index Seguro
                    val_sem = dados.get("Semestre", "")
                    idx_sem = LISTA_SEMESTRES.index(val_sem) if val_sem in LISTA_SEMESTRES else 0
                    new_sem = c1.selectbox("Semestre", LISTA_SEMESTRES, index=idx_sem)
                    
                    val_curr = dados.get("Curriculo", "")
                    idx_curr = LISTA_CURRICULOS.index(val_curr) if val_curr in LISTA_CURRICULOS else 0
                    new_curr = c2.radio("Currículo", LISTA_CURRICULOS, index=idx_curr)
                    
                    val_pet = dados.get("Petiano_Responsavel", "")
                    idx_pet = LISTA_PETIANOS.index(val_pet) if val_pet in LISTA_PETIANOS else 0
                    new_pet = st.selectbox("Responsável pela Transcrição", LISTA_PETIANOS, index=idx_pet)

                    st.markdown("---")
                    st.subheader("2. Correção de Notas Específicas")
                    st.info("Selecione a competência/disciplina abaixo para corrigir a nota lançada.")
                    
                    # Filtra colunas de nota
                    cols_notas = [c for c in df.columns if c not in ['Nome', 'Matricula', 'Data_Registro', 'Semestre', 'Curriculo', 'Petiano_Responsavel'] and not c.startswith("Obs") and not c.startswith("Auto") and not c.startswith("Contribuição") and not c.startswith("Exemplos") and not c.startswith("Competências") and not c.startswith("Plano") and not c.startswith("Comentários") and not c.startswith("Observações")]
                    
                    col_edit = st.selectbox("Escolha o campo para editar:", cols_notas)
                    
                    val_atual = dados.get(col_edit, "N/A")
                    if val_atual not in ["N/A", "0", "1", "2", "3", "4", "5"]: val_atual = "N/A"
                    
                    new_val = st.select_slider(f"Nova Nota para: {col_edit}", options=["N/A", "0", "1", "2", "3", "4", "5"], value=val_atual)
                    
                    st.markdown("---")
                    if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        df.at[idx, "Nome"] = new_nome
                        df.at[idx, "Matricula"] = new_mat
                        df.at[idx, "Semestre"] = new_sem
                        df.at[idx, "Curriculo"] = new_curr
                        df.at[idx, "Petiano_Responsavel"] = new_pet
                        df.at[idx, col_edit] = new_val
                        
                        df.to_csv(ARQUIVO_DB, index=False)
                        st.success("Registro atualizado com sucesso!")
                        st.rerun()
                    
        except Exception as e: st.error(f"Erro: {e}")

# ==============================================================================
# LÓGICA 3: PAINEL GERENCIAL
# ==============================================================================
elif modo_operacao == "📊 Painel Gerencial":
    st.markdown("### 📊 INDICADORES DE DESEMPENHO")
    
    if os.path.exists(ARQUIVO_DB):
        try:
            # Lê tudo como string primeiro para segurança
            df = pd.read_csv(ARQUIVO_DB, dtype=str)
            
            # FILTRO POR SEMESTRE
            sems_db = sorted(list(df['Semestre'].unique())) if 'Semestre' in df.columns else []
            filtro_sem = st.sidebar.selectbox("Filtrar por Semestre:", ["Todos"] + sems_db)
            
            if filtro_sem != "Todos":
                df = df[df['Semestre'] == filtro_sem]

            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Formulários", len(df))
            
            # Separa colunas de notas
            ignorar = ['Nome', 'Matricula', 'Semestre', 'Curriculo', 'Data_Registro', 'Petiano_Responsavel']
            cols_notas = [c for c in df.columns if c not in ignorar and not c.startswith("Obs") and not c.startswith("Auto") and not c.startswith("Contribuição") and not c.startswith("Exemplos") and not c.startswith("Competências") and not c.startswith("Plano") and not c.startswith("Comentários") and not c.startswith("Observações")]
            
            # Converte para numérico (N/A vira NaN)
            df_nums = df[cols_notas].apply(pd.to_numeric, errors='coerce')
            
            if not df_nums.empty:
                todos_valores = df_nums.stack()
                media = todos_valores.mean()
                desvio = todos_valores.std()
                
                c2.metric("Média Geral (Válidas)", f"{media:.2f}/5.0")
                c3.metric("Desvio Padrão", f"{desvio:.2f}")
            
            if 'Data_Registro' in df.columns:
                last = pd.to_datetime(df['Data_Registro']).max()
                c4.metric("Última Atividade", last.strftime("%d/%m %H:%M"))
            
            st.markdown("---")
            
            # --- SEÇÃO DE GRÁFICOS POR BLOCOS ---
            st.markdown("#### 📈 Análise por Blocos de Competência")
            
            grupos_analise = {
                "Competências Gerais": ["1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. "],
                "Competências Específicas": ["9. ", "10. ", "11. ", "12. ", "13. ", "14. ", "15. ", "16. ", "17. ", "18. ", "19. "],
                "Disciplinas Básicas": ["Cálculo", "Física", "Química", "Termo", "FT", "MecFlu"],
                "Disciplinas Profissionais": ["OpUnit", "Reatores", "Controle", "Projetos"],
                "Disciplinas Avançadas": ["Econ", "Gestão", "Amb", "Seg", "Lab", "Estágio", "Bio", "Petro", "Poli", "Cat", "Sim", "Otim", "TCC"]
            }

            for titulo_grupo, palavras_chave in grupos_analise.items():
                cols_grupo = [c for c in cols_notas if any(palavra in c for palavra in palavras_chave)]
                
                if cols_grupo:
                    df_grupo = df[cols_grupo].apply(pd.to_numeric, errors='coerce')
                    medias_grupo = df_grupo.mean().sort_values(ascending=True)
                    
                    if not medias_grupo.empty:
                        with st.expander(f"📊 {titulo_grupo}", expanded=False):
                            fig = px.bar(
                                medias_grupo, 
                                orientation='h', 
                                x=medias_grupo.values, 
                                y=medias_grupo.index,
                                text_auto='.2f',
                                labels={'index': '', 'x': 'Média'},
                                color=medias_grupo.values,
                                # CORES DO PET: Cinza -> Dourado -> Azul
                                color_continuous_scale=[(0, '#cfd8dc'), (0.5, '#dba800'), (1, '#002060')]
                            )
                            fig.update_layout(
                                height=max(400, len(medias_grupo)*30),
                                paper_bgcolor='rgba(0,0,0,0)', 
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(family="Segoe UI, sans-serif", size=12),
                                coloraxis_showscale=False
                            )
                            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.markdown("#### Detalhamento")
            st.dataframe(df, use_container_width=True, height=500)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Backup (Excel)", csv, f"sac_backup_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        except Exception as e: st.error(f"Erro: {e}")
    else:
        st.info("Nenhum dado.")
