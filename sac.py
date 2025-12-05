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
    }

    /* MODO CLARO */
    @media (prefers-color-scheme: light) {
        .stApp { background-color: #ffffff !important; }
        .pergunta-card { background-color: #fcfcfc !important; border-left: 5px solid #002060 !important; border: 1px solid #e0e0e0 !important; }
        .manual-box { background-color: #f0f2f6 !important; border: 1px solid #ddd !important; }
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

    /* CAIXAS DE AJUDA */
    .manual-box { padding: 15px; border-radius: 8px; margin-bottom: 15px; }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CABEÇALHO
# ==============================================================================
st.markdown("""
    <div style="text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid rgba(128,128,128,0.2);">
        <h1 style="margin: 0; font-size: 2.5rem;">S.A.C.</h1>
        <div style="font-size: 1.2rem; font-weight: 600; opacity: 0.8;">SISTEMA DE AVALIAÇÃO CURRICULAR - MÓDULO DE TRANSCRIÇÃO</div>
        <div style="font-size: 0.9rem; opacity: 0.6; margin-top: 5px;">PET ENGENHARIA QUÍMICA - UNIVERSIDADE FEDERAL DO CEARÁ</div>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LÓGICA DE BACKUP E ESTADO (CRUCIAL)
# ==============================================================================

# Seções do fluxo de transcrição (Sem o Painel Gerencial aqui!)
SECOES = [
    "1. Competências Gerais", 
    "2. Competências Específicas", 
    "3. Disciplinas Básicas", 
    "4. Disciplinas Profissionais", 
    "5. Disciplinas Avançadas", 
    "6. Reflexão Final (Obrigatória)"
]

# Inicializa Chaves de Controle
if 'form_key' not in st.session_state: st.session_state.form_key = 0
if 'navegacao_atual' not in st.session_state: st.session_state.navegacao_atual = SECOES[0]

def carregar_backup():
    """Restaura dados do JSON para o Session State se o arquivo existir."""
    if os.path.exists(ARQUIVO_BACKUP):
        try:
            with open(ARQUIVO_BACKUP, "r", encoding='utf-8') as f:
                dados = json.load(f)
                for k, v in dados.items():
                    # Só restaura se a chave pertencer ao formulário atual
                    if k.endswith(f"_{st.session_state.form_key}"): 
                        st.session_state[k] = v
        except: pass

# Tenta carregar backup na inicialização
if 'backup_restaurado' not in st.session_state:
    carregar_backup()
    st.session_state.backup_restaurado = True

def salvar_estado():
    """Salva todo o Session State relevante no arquivo JSON."""
    try:
        # Filtra chaves relevantes (identificação + notas + obs)
        dados_salvar = {
            k: v for k, v in st.session_state.items() 
            if (k.startswith("nota_") or k.startswith("obs_") or k.startswith("ident_"))
            and isinstance(v, (str, int, float, bool))
        }
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
    st.session_state.form_key += 1 # Incrementa ID do formulário (reseta widgets)
    st.session_state.navegacao_atual = SECOES[0]
    if os.path.exists(ARQUIVO_BACKUP):
        try: os.remove(ARQUIVO_BACKUP)
        except: pass

def obter_hora_ceara():
    fuso = timezone(timedelta(hours=-3))
    return datetime.now(fuso).strftime("%Y-%m-%d %H:%M:%S")

def renderizar_pergunta(texto_pergunta, id_unica):
    """Renderiza e vincula diretamente ao session_state."""
    k_suffix = st.session_state.form_key
    
    with st.container():
        st.markdown(f"""<div class="pergunta-card"><div class="pergunta-texto">{texto_pergunta}</div></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            val = st.select_slider(
                "Nível de Competência", 
                options=["N/A", "0", "1", "2", "3", "4", "5"], 
                value="N/A", # Padrão
                key=f"nota_{id_unica}_{k_suffix}",
                help="Selecione 'N/A' se vazio."
            )
        with c2:
            obs = st.text_input(
                "Transcrição de Obs.", 
                placeholder="Comentários...", 
                key=f"obs_{id_unica}_{k_suffix}"
            )
    return val, obs

# ==============================================================================
# 5. BARRA LATERAL (IDENTIFICAÇÃO)
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ MODO DE OPERAÇÃO")
    # Painel Gerencial agora é um MODO separado, não uma aba do wizard
    modo_operacao = st.radio("Ação:", ["📝 Nova Transcrição", "📊 Painel Gerencial"], label_visibility="collapsed")
    st.markdown("---")

    if modo_operacao == "📝 Nova Transcrição":
        tab_id, tab_manual = st.tabs(["👤 Identificação", "📘 Manual"])
        
        with tab_id:
            st.info("Preencha conforme o papel.")
            k_sfx = st.session_state.form_key
            
            # Usando prefixo 'ident_' para identificar no salvamento
            st.selectbox("Responsável", sorted(["", "Ana Carolina", "Ana Clara", "Ana Júlia", "Eric Rullian", "Gildelandio Junior", "Lucas Mossmann (trainee)", "Pedro Paulo"]), key=f"ident_pet_{k_sfx}")
            st.text_input("Nome do Discente", key=f"ident_nome_{k_sfx}")
            st.text_input("Matrícula", key=f"ident_mat_{k_sfx}")
            st.selectbox("Semestre", [f"{i}º Semestre" for i in range(1, 11)], key=f"ident_sem_{k_sfx}")
            st.radio("Matriz", ["Novo (2023.1)", "Antigo (2005.1)"], key=f"ident_curr_{k_sfx}")
            
            st.success("✅ Backup Ativo")
            if st.button("🗑️ Limpar Formulário"):
                limpar_formulario()
                st.rerun()

        with tab_manual:
            st.markdown("### 📘 GUIA DE TRANSCRIÇÃO")
            st.markdown('<div class="manual-box">', unsafe_allow_html=True)
            st.markdown("**1. ESCALA E 'N/A'**")
            st.caption("Use **N/A** para campos em branco, rasurados ou ilegíveis. O N/A não entra no cálculo da média (não conta como zero).")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="manual-box">', unsafe_allow_html=True)
            st.markdown("**2. TEXTOS OBRIGATÓRIOS**")
            st.caption("A seção **REFLEXÃO FINAL** é obrigatória. Se o aluno deixou em branco, você DEVE digitar **'EM BRANCO'** para conseguir salvar.")
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# LÓGICA 1: WIZARD DE TRANSCRIÇÃO
# ==============================================================================
if modo_operacao == "📝 Nova Transcrição":
    # Menu Superior Controlado
    secao_ativa = st.radio("Etapas:", SECOES, horizontal=True, key="navegacao_atual", label_visibility="collapsed")
    st.markdown("---")

    # --- RENDERIZAÇÃO DAS SEÇÕES ---
    if secao_ativa == SECOES[0]:
        st.markdown("### 1. COMPETÊNCIAS TÉCNICAS E GERAIS")
        renderizar_pergunta("1. Projetar e conduzir experimentos e interpretar resultados", "q1")
        renderizar_pergunta("2. Desenvolver e/ou utilizar novas ferramentas e técnicas", "q2")
        renderizar_pergunta("3. Conceber, projetar e analisar sistemas, produtos e processos", "q3")
        renderizar_pergunta("4. Formular, conceber e avaliar soluções para problemas de engenharia", "q4")
        renderizar_pergunta("5. Analisar e compreender fenômenos físicos e químicos através de modelos", "q5")
        renderizar_pergunta("6. Comunicar-se nas formas escrita, oral e gráfica", "q6")
        renderizar_pergunta("7. Trabalhar e liderar equipes profissionais e multidisciplinares", "q7")
        renderizar_pergunta("8. Aplicar ética e legislação no exercício profissional", "q8")
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav1")
            st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[1]:
        st.markdown("### 2. COMPETÊNCIAS ESPECÍFICAS")
        renderizar_pergunta("9. Aplicar conhecimentos matemáticos, científicos e tecnológicos", "q9")
        renderizar_pergunta("10. Compreender e modelar transferência de quantidade de movimento, calor e massa", "q10")
        renderizar_pergunta("11. Aplicar conhecimentos de fenômenos de transporte ao projeto", "q11")
        renderizar_pergunta("12. Compreender mecanismos de transformação da matéria e energia", "q12")
        renderizar_pergunta("13. Projetar sistemas de recuperação, separação e purificação", "q13")
        renderizar_pergunta("14. Compreender mecanismos cinéticos de reações químicas", "q14")
        renderizar_pergunta("15. Projetar e otimizar sistemas reacionais e reatores", "q15")
        renderizar_pergunta("16. Projetar sistemas de controle de processos industriais", "q16")
        renderizar_pergunta("17. Projetar e otimizar plantas industriais (ambiental/segurança)", "q17")
        st.markdown("#### Eixos de Formação Prática")
        renderizar_pergunta("18. Aplicação de conhecimentos em projeto básico e dimensionamento", "q18")
        renderizar_pergunta("19. Execução de projetos de produção e melhorias de processos", "q19")
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav2")
            st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[2]:
        st.markdown("### 3. DISCIPLINAS BÁSICAS")
        with st.expander("CÁLCULO E FÍSICA", expanded=True):
            renderizar_pergunta("21. Analisar grandes volumes de dados", "calc_21")
            renderizar_pergunta("52. Formação Básica (cálculo, física, química, estatística)", "calc_52")
            renderizar_pergunta("22. Analisar criticamente a operação e manutenção de sistemas", "fis_22")
            renderizar_pergunta("53. Ciência da Engenharia (mecânica, resistência)", "fis_53")
        with st.expander("QUÍMICA E TERMO", expanded=True):
            renderizar_pergunta("23. Aplicar conhecimentos de transformação a processos", "qui_23")
            renderizar_pergunta("24. Conceber e desenvolver produtos e processos", "qui_24")
            renderizar_pergunta("25. Projetar sistemas de suprimento energético", "termo_25")
            renderizar_pergunta("54. Ciência da Eng. Química (termodinâmica)", "termo_54")
        with st.expander("FENÔMENOS E MECFLU", expanded=True):
            renderizar_pergunta("26. Aplicar conhecimentos de fenômenos de transporte", "ft_26")
            renderizar_pergunta("27. Comunicar-se tecnicamente e usar recursos gráficos", "ft_27")
            renderizar_pergunta("28. Implantar, implementar e controlar soluções", "mecflu_28")
            renderizar_pergunta("29. Operar e supervisionar instalações", "mecflu_29")
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav3")
            st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[3]:
        st.markdown("### 4. DISCIPLINAS PROFISSIONALIZANTES")
        with st.expander("OPERAÇÕES UNITÁRIAS", expanded=True):
            renderizar_pergunta("30. Inspecionar e coordenar manutenção", "op1_30")
            renderizar_pergunta("55. Tecnologia Industrial", "op1_55")
            renderizar_pergunta("31. Elaborar estudos de impactos ambientais", "op2_31")
            renderizar_pergunta("32. Projetar processos de tratamento ambiental", "op2_32")
        with st.expander("REATORES QUÍMICOS", expanded=True):
            renderizar_pergunta("33. Gerir recursos estratégicos na produção", "reat_33")
            renderizar_pergunta("34. Aplicar modelos de produção e controle de qualidade", "reat_34")
        with st.expander("CONTROLE E PROJETOS", expanded=True):
            renderizar_pergunta("35. Controle e supervisão de instalações", "ctrl_35")
            renderizar_pergunta("36. Gestão de empreendimentos industriais", "ctrl_36")
            renderizar_pergunta("56. Projetos Industriais e Gestão", "proj_56")
            renderizar_pergunta("57. Ética, Meio Ambiente e Humanidades", "proj_57")
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav4")
            st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[4]:
        st.markdown("### 5. AVANÇADAS E COMPLEMENTARES")
        with st.expander("GESTÃO E AMBIENTAL", expanded=True):
            renderizar_pergunta("37. Eng. Econômica: Aprender novos conceitos", "econ_37")
            renderizar_pergunta("38. Eng. Econômica: Visão global", "econ_38")
            renderizar_pergunta("39. Gestão Produção: Comprometimento", "gest_39")
            renderizar_pergunta("40. Gestão Produção: Resultados", "gest_40")
            renderizar_pergunta("41. Eng. Ambiental: Inovação", "amb_41")
            renderizar_pergunta("42. Eng. Ambiental: Situações novas", "amb_42")
            renderizar_pergunta("43. Segurança: Incertezas", "seg_43")
            renderizar_pergunta("44. Segurança: Decisão", "seg_44")
        with st.expander("PRÁTICAS (LAB/ESTÁGIO)", expanded=True):
            renderizar_pergunta("45. Laboratório: Criatividade", "lab_45")
            renderizar_pergunta("46. Laboratório: Relacionamento", "lab_46")
            renderizar_pergunta("47. Estágio: Autocontrole emocional", "est_47")
            renderizar_pergunta("48. Estágio: Capacidade empreendedora", "est_48")
        with st.expander("OPTATIVAS E INTEGRADORAS", expanded=True):
            renderizar_pergunta("49. Biotec: Analisar dados", "bio_49")
            renderizar_pergunta("50. Biotec: Novas ferramentas", "bio_50")
            renderizar_pergunta("51. Petróleo: Recuperação", "petro_51")
            renderizar_pergunta("52. Petróleo: Reatores", "petro_52")
            renderizar_pergunta("57. Simulação: Dados", "sim_57")
            renderizar_pergunta("58. Simulação: Comunicação", "sim_58")
            renderizar_pergunta("59. Otimização: Soluções", "otim_59")
            renderizar_pergunta("60. Otimização: Modelos", "otim_60")
            renderizar_pergunta("61. TCC: Comunicação", "tcc_61")
            renderizar_pergunta("62. TCC: Liderança", "tcc_62")
        
        st.markdown("---")
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav5")
            st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[5]: # Final
        st.markdown("### 6. REFLEXÃO FINAL")
        st.warning("⚠️ **ATENÇÃO:** O preenchimento desta seção é OBRIGATÓRIO para salvar.")
        
        renderizar_pergunta("20. Capacidade de aprender rapidamente novos conceitos", "q20_indiv")
        
        st.markdown("#### TRANSCRIÇÃO DAS RESPOSTAS ABERTAS")
        
        # Recupera chave atual
        k = st.session_state.form_key
        
        # Campos de Texto (Obrigatórios na validação)
        st.text_area("Pontos Fortes (Obrigatório)", key=f"obs_fortes_{k}")
        st.text_area("Pontos a Desenvolver (Obrigatório)", key=f"obs_fracos_{k}")
        st.text_area("Contribuição Prática", key=f"obs_prat_{k}")
        st.text_area("Exemplos de Aplicação", key=f"obs_ex_{k}")
        st.text_area("Competências Futuras", key=f"obs_fut1_{k}")
        st.text_area("Plano de Desenvolvimento", key=f"obs_fut2_{k}")
        st.text_area("Comentários Finais", key=f"obs_final_{k}")

        st.markdown("---")
        st.markdown('<div class="botao-final">', unsafe_allow_html=True)
        if st.button("💾 FINALIZAR E SALVAR REGISTRO", type="primary"):
            # 1. Recuperar dados do session_state
            k = st.session_state.form_key
            dados = {}
            
            # Dados de Identificação
            dados["Petiano_Responsavel"] = st.session_state.get(f"ident_pet_{k}", "")
            dados["Nome"] = st.session_state.get(f"ident_nome_{k}", "")
            dados["Matricula"] = st.session_state.get(f"ident_mat_{k}", "")
            dados["Semestre"] = st.session_state.get(f"ident_sem_{k}", "")
            dados["Curriculo"] = st.session_state.get(f"ident_curr_{k}", "")
            dados["Data_Registro"] = obter_hora_ceara()
            
            # Dados das Perguntas (Varredura)
            for key in st.session_state:
                if key.endswith(f"_{k}"):
                    if key.startswith("nota_"):
                        col_name = key.replace("nota_", "").replace(f"_{k}", "")
                        dados[col_name] = st.session_state[key]
                    elif key.startswith("obs_"):
                        col_name = "Obs_" + key.replace("obs_", "").replace(f"_{k}", "")
                        dados[col_name] = st.session_state[key]

            # 2. Validação
            erros = []
            if not dados.get("Nome"): erros.append("Nome do Discente")
            if not dados.get("Petiano_Responsavel"): erros.append("Petiano Responsável")
            if not dados.get("Obs_fortes") or not dados.get("Obs_fracos"):
                erros.append("Campos de Reflexão (Digite 'EM BRANCO' se vazio)")

            if erros:
                st.error(f"❌ IMPOSSÍVEL SALVAR: {', '.join(erros)}")
            else:
                try:
                    df_new = pd.DataFrame([dados])
                    if os.path.exists(ARQUIVO_DB):
                        df_new.to_csv(ARQUIVO_DB, mode='a', header=False, index=False)
                    else:
                        df_new.to_csv(ARQUIVO_DB, mode='w', header=True, index=False)
                    
                    st.balloons()
                    st.success(f"✅ Registro de {dados['Nome']} salvo com sucesso!")
                    limpar_formulario()
                    st.rerun()
                except PermissionError:
                    st.error("❌ ERRO: Feche o arquivo Excel aberto.")
                except Exception as e:
                    st.error(f"❌ ERRO: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Auto-Save Executa a cada interação
    salvar_estado()

# ==============================================================================
# LÓGICA 2: PAINEL GERENCIAL
# ==============================================================================
elif modo_operacao == "📊 Painel Gerencial":
    st.markdown("### 📊 INDICADORES DE DESEMPENHO")
    
    if os.path.exists(ARQUIVO_DB):
        try:
            df = pd.read_csv(ARQUIVO_DB, dtype={'Matricula': str})
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Formulários", len(df))
            
            # Filtro Inteligente: Remove colunas que não são notas
            ignorar = ['Nome', 'Matricula', 'Semestre', 'Curriculo', 'Data_Registro', 'Petiano_Responsavel']
            cols_notas = [c for c in df.columns if c not in ignorar and not c.startswith("Obs_")]
            
            # Converte "N/A" para NaN e calcula média ignorando-os
            df_nums = df[cols_notas].apply(pd.to_numeric, errors='coerce')
            
            if not df_nums.empty:
                media = df_nums.mean().mean()
                c2.metric("Média Geral (Exclui N/A)", f"{media:.2f}/5.0")
            
            if 'Data_Registro' in df.columns:
                last = pd.to_datetime(df['Data_Registro']).max()
                c3.metric("Última Atividade", last.strftime("%d/%m %H:%M"))
            
            st.markdown("---")
            st.markdown("#### Detalhamento")
            st.dataframe(df, use_container_width=True, height=500)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Backup (Excel)", csv, f"sac_backup_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        except Exception as e: st.error(f"Erro no banco: {e}")
    else:
        st.info("Nenhum dado.")
