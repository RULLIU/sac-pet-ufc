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
# 2. ESTILO VISUAL (CSS)
# ==============================================================================
st.markdown("""
    <style>
    /* RESET */
    .stApp { background-color: #ffffff !important; font-family: 'Segoe UI', sans-serif; }
    p, label, span, div, li, .stMarkdown { color: #2c3e50 !important; }
    h1, h2, h3, h4, h5, h6 { color: #002060 !important; font-weight: 800 !important; text-transform: uppercase; }

    /* MENU DE NAVEGAÇÃO (SUBSTITUI AS ABAS) */
    div[role="radiogroup"] {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #ddd;
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    
    /* BOTÃO AVANÇAR (VERDE DESTAQUE) */
    .stButton button {
        border-radius: 6px;
        height: 3em;
        font-weight: 700;
        text-transform: uppercase;
        width: 100%;
        transition: 0.3s;
    }
    
    /* Botão Principal (Salvar Final) */
    .botao-final button {
        background-color: #002060 !important;
        color: white !important;
        height: 4.5em;
    }
    
    /* Botão Avançar (Secundário) */
    .botao-avancar button {
        background-color: #ffffff !important;
        color: #002060 !important;
        border: 2px solid #002060 !important;
    }
    .botao-avancar button:hover {
        background-color: #002060 !important;
        color: white !important;
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

    /* MENUS */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CABEÇALHO
# ==============================================================================
st.markdown("""
    <div style="text-align: center; border-bottom: 4px solid #002060; padding-bottom: 20px; margin-bottom: 30px;">
        <div style="font-size: 2.5rem; color: #002060; font-weight: 800;">S.A.C.</div>
        <div style="font-size: 1.2rem; color: #555; font-weight: 600;">SISTEMA DE AVALIAÇÃO CURRICULAR</div>
        <div style="font-size: 0.9rem; color: #666;">DEPARTAMENTO DE ENGENHARIA QUÍMICA - UFC</div>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. GERENCIAMENTO DE ESTADO E NAVEGAÇÃO
# ==============================================================================
# Lista Oficial de Seções (Ordem Lógica)
SECOES = [
    "1. Competências Gerais", 
    "2. Competências Específicas", 
    "3. Disciplinas Básicas", 
    "4. Disciplinas Profissionais", 
    "5. Disciplinas Avançadas", 
    "6. Reflexão Final", 
    "📊 Painel Gerencial"
]

if 'form_key' not in st.session_state:
    st.session_state.form_key = 0

# Inicializa a navegação na primeira seção se não existir
if 'navegacao_atual' not in st.session_state:
    st.session_state.navegacao_atual = SECOES[0]

def navegar_proxima():
    """Função para pular para a próxima aba automaticamente."""
    try:
        indice_atual = SECOES.index(st.session_state.navegacao_atual)
        if indice_atual < len(SECOES) - 1:
            st.session_state.navegacao_atual = SECOES[indice_atual + 1]
    except:
        pass

def limpar_formulario():
    st.session_state.form_key += 1
    st.session_state.navegacao_atual = SECOES[0] # Volta para o início
    if os.path.exists(ARQUIVO_BACKUP):
        try: os.remove(ARQUIVO_BACKUP)
        except: pass

def obter_hora_ceara():
    fuso = timezone(timedelta(hours=-3))
    return datetime.now(fuso).strftime("%Y-%m-%d %H:%M:%S")

def renderizar_pergunta(texto_pergunta, id_unica):
    """Gera o bloco visual da pergunta."""
    with st.container():
        st.markdown(f"<div class='pergunta-card'><div class='pergunta-texto'>{texto_pergunta}</div></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([0.60, 0.40])
        with c1:
            val = st.select_slider("Nível de Competência", options=["0", "1", "2", "3", "4", "5"], value="0", key=f"nota_{id_unica}_{st.session_state.form_key}")
        with c2:
            obs = st.text_input("Justificativa e Observações", placeholder="Comentários...", key=f"obs_{id_unica}_{st.session_state.form_key}")
    return int(val), obs

# ==============================================================================
# 5. BARRA LATERAL
# ==============================================================================
respostas = {}

with st.sidebar:
    st.markdown("### 👤 IDENTIFICAÇÃO")
    lista_petianos = ["", "Ana Carolina", "Ana Clara", "Ana Júlia", "Eric Rullian", "Gildelandio Junior", "Lucas Mossmann (trainee)", "Pedro Paulo"]
    respostas["Petiano_Responsavel"] = st.selectbox("Petiano Responsável", lista_petianos, key=f"pet_{st.session_state.form_key}")
    respostas["Nome"] = st.text_input("Nome do Discente", key=f"nome_{st.session_state.form_key}")
    respostas["Matricula"] = st.text_input("Matrícula", key=f"mat_{st.session_state.form_key}")
    respostas["Semestre"] = st.selectbox("Semestre Atual", [f"{i}º Semestre" for i in range(1, 11)], key=f"sem_{st.session_state.form_key}")
    respostas["Curriculo"] = st.radio("Matriz", ["Novo (2023.1)", "Antigo (2005.1)"], key=f"curr_{st.session_state.form_key}")
    respostas["Data_Registro"] = obter_hora_ceara()
    st.markdown("---")
    st.info("💡 As seções avançam automaticamente ao clicar em 'Próximo'.")

# ==============================================================================
# 6. MENU DE NAVEGAÇÃO SUPERIOR (INTERATIVO)
# ==============================================================================
# Isso substitui as st.tabs antigas por um controle que podemos mudar via código
secao_ativa = st.radio(
    "", 
    SECOES, 
    horizontal=True, 
    key="navegacao_atual", # Vinculado ao session_state para permitir troca automática
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
    respostas["4. Prob. Engenharia"], respostas["Obs_4"] = renderizar_pergunta("4. Formular, conceber e avaliar soluções para problemas de engenharia", "q4")
    respostas["5. Modelagem"], respostas["Obs_5"] = renderizar_pergunta("5. Analisar e compreender fenômenos físicos e químicos através de modelos", "q5")
    respostas["6. Comunicação"], respostas["Obs_6"] = renderizar_pergunta("6. Comunicar-se nas formas escrita, oral e gráfica", "q6")
    respostas["7. Trab. Equipe"], respostas["Obs_7"] = renderizar_pergunta("7. Trabalhar e liderar equipes profissionais e multidisciplinares", "q7")
    respostas["8. Ética"], respostas["Obs_8"] = renderizar_pergunta("8. Aplicar ética e legislação no exercício profissional", "q8")
    
    st.markdown("---")
    # Botão de Avançar
    col_nav1, col_nav2 = st.columns([0.8, 0.2])
    with col_nav2:
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("➡️ PRÓXIMO BLOCO", on_click=navegar_proxima, key="btn_nav_1")
        st.markdown('</div>', unsafe_allow_html=True)

# --- SEÇÃO 2 ---
elif secao_ativa == SECOES[1]:
    st.markdown("### 2. COMPETÊNCIAS ESPECÍFICAS")
    respostas["9. Fundamentos Mat."], respostas["Obs_9"] = renderizar_pergunta("9. Aplicar conhecimentos matemáticos, científicos e tecnológicos", "q9")
    respostas["10. Modelagem Transp."], respostas["Obs_10"] = renderizar_pergunta("10. Compreender e modelar transferência de quantidade de movimento, calor e massa", "q10")
    respostas["11. Aplic. Transp."], respostas["Obs_11"] = renderizar_pergunta("11. Aplicar conhecimentos de fenômenos de transporte ao projeto", "q11")
    respostas["12. Transf. Matéria"], respostas["Obs_12"] = renderizar_pergunta("12. Compreender mecanismos de transformação da matéria e energia", "q12")
    respostas["13. Separação"], respostas["Obs_13"] = renderizar_pergunta("13. Projetar sistemas de recuperação, separação e purificação", "q13")
    respostas["14. Cinética"], respostas["Obs_14"] = renderizar_pergunta("14. Compreender mecanismos cinéticos de reações químicas", "q14")
    respostas["15. Reatores"], respostas["Obs_15"] = renderizar_pergunta("15. Projetar e otimizar sistemas reacionais e reatores", "q15")
    respostas["16. Controle"], respostas["Obs_16"] = renderizar_pergunta("16. Projetar sistemas de controle de processos industriais", "q16")
    respostas["17. Projetos Ind."], respostas["Obs_17"] = renderizar_pergunta("17. Projetar e otimizar plantas industriais (ambiental/segurança)", "q17")
    st.markdown("### EIXOS PRÁTICOS")
    respostas["18. Projeto Básico"], respostas["Obs_18"] = renderizar_pergunta("18. Aplicação de conhecimentos em projeto básico e dimensionamento", "q18")
    respostas["19. Melhoria Proc."], respostas["Obs_19"] = renderizar_pergunta("19. Execução de projetos de produção e melhorias de processos", "q19")
    
    st.markdown("---")
    col_nav1, col_nav2 = st.columns([0.8, 0.2])
    with col_nav2:
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("➡️ PRÓXIMO BLOCO", on_click=navegar_proxima, key="btn_nav_2")
        st.markdown('</div>', unsafe_allow_html=True)

# --- SEÇÃO 3 ---
elif secao_ativa == SECOES[2]:
    st.markdown("### 3. DISCIPLINAS BÁSICAS")
    with st.expander("CÁLCULO E FÍSICA", expanded=True):
        respostas["Cálculo: Dados"], respostas["Obs_C1"] = renderizar_pergunta("21. Analisar grandes volumes de dados", "calc_21")
        respostas["Cálculo: Formação"], respostas["Obs_C2"] = renderizar_pergunta("52. Formação Básica", "calc_52")
        respostas["Física: Operação"], respostas["Obs_F1"] = renderizar_pergunta("22. Analisar criticamente a operação e manutenção de sistemas", "fis_22")
        respostas["Física: Ciência"], respostas["Obs_F2"] = renderizar_pergunta("53. Ciência da Engenharia", "fis_53")
    with st.expander("QUÍMICA E TERMO", expanded=True):
        respostas["Química: Transf."], respostas["Obs_Q1"] = renderizar_pergunta("23. Aplicar conhecimentos de transformação a processos", "qui_23")
        respostas["Química: Desenv."], respostas["Obs_Q2"] = renderizar_pergunta("24. Conceber e desenvolver produtos e processos", "qui_24")
        respostas["Termo: Energia"], respostas["Obs_T1"] = renderizar_pergunta("25. Projetar sistemas de suprimento energético", "termo_25")
        respostas["Termo: Ciência"], respostas["Obs_T2"] = renderizar_pergunta("54. Ciência da Eng. Química", "termo_54")
    with st.expander("FENÔMENOS DE TRANSPORTE", expanded=True):
        respostas["FT: Aplicação"], respostas["Obs_FT1"] = renderizar_pergunta("26. Aplicar conhecimentos de fenômenos de transporte", "ft_26")
        respostas["FT: Gráficos"], respostas["Obs_FT2"] = renderizar_pergunta("27. Comunicar-se tecnicamente e usar recursos gráficos", "ft_27")
        respostas["MecFlu: Soluções"], respostas["Obs_MF1"] = renderizar_pergunta("28. Implantar, implementar e controlar soluções", "mecflu_28")
        respostas["MecFlu: Supervisão"], respostas["Obs_MF2"] = renderizar_pergunta("29. Operar e supervisionar instalações", "mecflu_29")
    
    st.markdown("---")
    col_nav1, col_nav2 = st.columns([0.8, 0.2])
    with col_nav2:
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("➡️ PRÓXIMO BLOCO", on_click=navegar_proxima, key="btn_nav_3")
        st.markdown('</div>', unsafe_allow_html=True)

# --- SEÇÃO 4 ---
elif secao_ativa == SECOES[3]:
    st.markdown("### 4. DISCIPLINAS PROFISSIONALIZANTES")
    with st.expander("OPERAÇÕES UNITÁRIAS", expanded=True):
        respostas["OpUnit: Manutenção"], respostas["Obs_O1"] = renderizar_pergunta("30. Inspecionar e coordenar manutenção", "op1_30")
        respostas["OpUnit: Tecnologia"], respostas["Obs_O1b"] = renderizar_pergunta("55. Tecnologia Industrial", "op1_55")
        respostas["OpUnit: Impacto"], respostas["Obs_O2"] = renderizar_pergunta("31. Elaborar estudos de impactos ambientais", "op2_31")
        respostas["OpUnit: Tratamento"], respostas["Obs_O2b"] = renderizar_pergunta("32. Projetar processos de tratamento ambiental", "op2_32")
    with st.expander("REATORES E CONTROLE", expanded=True):
        respostas["Reatores: Recursos"], respostas["Obs_R1"] = renderizar_pergunta("33. Gerir recursos estratégicos na produção", "reat_33")
        respostas["Reatores: Qualidade"], respostas["Obs_R2"] = renderizar_pergunta("34. Aplicar modelos de produção e qualidade", "reat_34")
        respostas["Controle: Supervisão"], respostas["Obs_Ct1"] = renderizar_pergunta("35. Controle e supervisão de instalações", "ctrl_35")
        respostas["Controle: Gestão"], respostas["Obs_Ct2"] = renderizar_pergunta("36. Gestão de empreendimentos industriais", "ctrl_36")
    with st.expander("PROJETOS", expanded=True):
        respostas["Projetos: Gestão"], respostas["Obs_Pr1"] = renderizar_pergunta("56. Projetos Industriais e Gestão", "proj_56")
        respostas["Projetos: Ética"], respostas["Obs_Pr2"] = renderizar_pergunta("57. Ética, Meio Ambiente e Humanidades", "proj_57")
    
    st.markdown("---")
    col_nav1, col_nav2 = st.columns([0.8, 0.2])
    with col_nav2:
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("➡️ PRÓXIMO BLOCO", on_click=navegar_proxima, key="btn_nav_4")
        st.markdown('</div>', unsafe_allow_html=True)

# --- SEÇÃO 5 ---
elif secao_ativa == SECOES[4]:
    st.markdown("### 5. DISCIPLINAS AVANÇADAS")
    with st.expander("GESTÃO E AMBIENTAL", expanded=True):
        respostas["Econ: Novos"], respostas["Obs_Ec1"] = renderizar_pergunta("37. Eng. Econômica: Aprender novos conceitos", "econ_37")
        respostas["Econ: Visão"], respostas["Obs_Ec2"] = renderizar_pergunta("38. Eng. Econômica: Visão global", "econ_38")
        respostas["Gestão: Compr."], respostas["Obs_G1"] = renderizar_pergunta("39. Gestão da Produção: Comprometimento", "gest_39")
        respostas["Gestão: Result."], respostas["Obs_G2"] = renderizar_pergunta("40. Gestão da Produção: Resultados", "gest_40")
        respostas["Amb: Inovação"], respostas["Obs_A1"] = renderizar_pergunta("41. Eng. Ambiental: Inovação", "amb_41")
        respostas["Amb: Situações"], respostas["Obs_A2"] = renderizar_pergunta("42. Eng. Ambiental: Situações novas", "amb_42")
        respostas["Seg: Incertezas"], respostas["Obs_S1"] = renderizar_pergunta("43. Segurança: Lidar com incertezas", "seg_43")
        respostas["Seg: Decisão"], respostas["Obs_S2"] = renderizar_pergunta("44. Segurança: Iniciativa e decisão", "seg_44")
    with st.expander("PRÁTICAS", expanded=True):
        respostas["Lab: Criatividade"], respostas["Obs_L1"] = renderizar_pergunta("45. Laboratório: Criatividade", "lab_45")
        respostas["Lab: Relacionam."], respostas["Obs_L2"] = renderizar_pergunta("46. Laboratório: Relacionamento", "lab_46")
        respostas["Estágio: Autocont."], respostas["Obs_E1"] = renderizar_pergunta("47. Estágio: Autocontrole emocional", "est_47")
        respostas["Estágio: Empreend."], respostas["Obs_E2"] = renderizar_pergunta("48. Estágio: Capacidade empreendedora", "est_48")
    with st.expander("OPTATIVAS E INTEGRADORAS", expanded=True):
        respostas["Bio: Dados"], respostas["Obs_B1"] = renderizar_pergunta("49. Biotecnologia: Analisar grandes volumes de dados", "bio_49")
        respostas["Bio: Ferram."], respostas["Obs_B2"] = renderizar_pergunta("50. Biotecnologia: Novas ferramentas", "bio_50")
        respostas["Petro: Recuper."], respostas["Obs_P1"] = renderizar_pergunta("51. Petróleo: Projetar sistemas de recuperação", "petro_51")
        respostas["Petro: Reatores"], respostas["Obs_P2"] = renderizar_pergunta("52. Petróleo: Projetar reatores", "petro_52")
        respostas["Sim: Dados"], respostas["Obs_Si1"] = renderizar_pergunta("57. Simulação: Analisar dados", "sim_57")
        respostas["Sim: Comun."], respostas["Obs_Si2"] = renderizar_pergunta("58. Simulação: Comunicação técnica", "sim_58")
        respostas["TCC: Comun."], respostas["Obs_Tc1"] = renderizar_pergunta("61. TCC: Comunicação escrita/oral", "tcc_61")
        respostas["TCC: Liderança"], respostas["Obs_Tc2"] = renderizar_pergunta("62. TCC: Liderar equipes", "tcc_62")
    
    st.markdown("---")
    col_nav1, col_nav2 = st.columns([0.8, 0.2])
    with col_nav2:
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("➡️ PRÓXIMO BLOCO", on_click=navegar_proxima, key="btn_nav_5")
        st.markdown('</div>', unsafe_allow_html=True)

# --- SEÇÃO 6 (FINAL) ---
elif secao_ativa == SECOES[5]:
    st.markdown("### 6. REFLEXÃO FINAL")
    respostas["20. Aprendizado Ágil"], respostas["Obs_20"] = renderizar_pergunta("20. Capacidade de aprender rapidamente novos conceitos", "q20_indiv")
    st.markdown("#### AUTOAVALIAÇÃO")
    respostas["Pontos Fortes"] = st.text_area("Pontos Fortes", key=f"fortes_{st.session_state.form_key}")
    respostas["Pontos a Desenvolver"] = st.text_area("Pontos a Desenvolver", key=f"fracos_{st.session_state.form_key}")
    st.markdown("#### PRÁTICA E FUTURO")
    respostas["Contribuição Prática"] = st.text_area("Contribuição das atividades", key=f"prat_{st.session_state.form_key}")
    respostas["Exemplos Práticos"] = st.text_area("Exemplos de aplicação", key=f"ex_{st.session_state.form_key}")
    respostas["Competências Futuras"] = st.text_area("Competências essenciais futuras", key=f"fut1_{st.session_state.form_key}")
    respostas["Plano Desenv."] = st.text_area("Plano de desenvolvimento", key=f"fut2_{st.session_state.form_key}")
    respostas["Comentários Finais"] = st.text_area("Comentários Finais", key=f"obsf_{st.session_state.form_key}")

    st.markdown("---")
    st.markdown('<div class="botao-final">', unsafe_allow_html=True)
    if st.button("💾 FINALIZAR E REGISTRAR AVALIAÇÃO", type="primary"):
        if not respostas["Nome"]:
            st.error("⚠️ ERRO: Preencha o NOME DO DISCENTE na barra lateral.")
        elif not respostas["Petiano_Responsavel"]:
            st.error("⚠️ ERRO: Selecione o PETIANO RESPONSÁVEL.")
        else:
            try:
                df_new = pd.DataFrame([respostas])
                if os.path.exists(ARQUIVO_DB):
                    df_new.to_csv(ARQUIVO_DB, mode='a', header=False, index=False)
                else:
                    df_new.to_csv(ARQUIVO_DB, mode='w', header=True, index=False)
                
                st.balloons()
                st.success(f"Sucesso! Avaliação de {respostas['Nome']} registrada.")
                limpar_formulario()
                st.rerun()
            except PermissionError:
                st.error("❌ ERRO: O arquivo Excel está aberto. Feche-o e tente novamente.")
            except Exception as e:
                st.error(f"❌ ERRO INESPERADO: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- AUTO-SAVE ---
try:
    with open(ARQUIVO_BACKUP, "w", encoding='utf-8') as f:
        json.dump(respostas, f, indent=4, ensure_ascii=False)
except: pass

# --- SEÇÃO 7 (DASHBOARD) ---
elif secao_ativa == SECOES[6]:
    st.markdown("### 📊 PAINEL DE INDICADORES")
    if os.path.exists(ARQUIVO_DB):
        try:
            df = pd.read_csv(ARQUIVO_DB, dtype={'Matricula': str})
            col1, col2, col3 = st.columns(3)
            col1.metric("Discentes Avaliados", len(df))
            
            # Filtro de colunas numéricas (Ignorando identificação)
            colunas_ignorar = ['Nome', 'Matricula', 'Semestre', 'Curriculo', 'Data_Registro', 'Petiano_Responsavel']
            colunas_numericas = [c for c in df.columns if c not in colunas_ignorar and not c.startswith("Obs") and not c.startswith("Auto") and not c.startswith("Justificativa") and not c.startswith("Contribuição") and not c.startswith("Exemplos") and not c.startswith("Competências") and not c.startswith("Plano") and not c.startswith("Comentários")]
            
            df_num = df[colunas_numericas].apply(pd.to_numeric, errors='coerce')
            if not df_num.empty:
                media_geral = df_num.mean().mean()
                col2.metric("Média Geral", f"{media_geral:.2f}/5.0")
            
            if 'Data_Registro' in df.columns:
                last_dt = pd.to_datetime(df['Data_Registro']).max()
                col3.metric("Última Atualização", last_dt.strftime("%d/%m/%Y às %H:%M"))
            
            st.markdown("---")
            st.markdown("#### Base de Dados Detalhada")
            st.dataframe(df, use_container_width=True, height=500)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Planilha Completa", csv, f"sac_relatorio_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        except Exception as e:
            st.error(f"Erro: {e}")
    else:
        st.info("Nenhum dado registrado.")
