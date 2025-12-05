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
# 2. ESTILO VISUAL (CSS)
# ==============================================================================
st.markdown("""
    <style>
    :root { --primary-color: #002060; }
    .stApp { font-family: 'Segoe UI', sans-serif; background-color: #ffffff; }
    
    /* Títulos */
    h1, h2, h3, h4 { color: var(--primary-color) !important; font-weight: 800 !important; text-transform: uppercase; }
    
    /* Modo Escuro */
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, h4 { color: #82b1ff !important; }
        .pergunta-card { background-color: #1e1e1e !important; border-left: 5px solid #82b1ff !important; }
    }

    /* Cards */
    .pergunta-card {
        background-color: #f8f9fa; border: 1px solid rgba(0,0,0,0.1);
        border-left: 5px solid #002060; border-radius: 8px; padding: 20px; margin-bottom: 25px;
    }
    .pergunta-texto { font-size: 1.1rem; font-weight: 700; margin-bottom: 15px; opacity: 0.95; }

    /* Botões */
    .stButton button { border-radius: 6px; font-weight: 700; text-transform: uppercase; height: 3.5em; width: 100%; transition: 0.3s; }
    .botao-avancar button { border: 2px solid #002060; color: #002060; background: transparent; }
    .botao-avancar button:hover { background: #002060; color: white; }
    .botao-final button { background: #002060 !important; color: white !important; border: none; }
    .botao-final button:hover { background: #003399 !important; transform: scale(1.02); }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. LÓGICA DE BACKUP E ESTADO (CORRIGIDA)
# ==============================================================================

# Função para Carregar Backup ao Iniciar
def carregar_backup():
    if os.path.exists(ARQUIVO_BACKUP):
        try:
            with open(ARQUIVO_BACKUP, "r", encoding='utf-8') as f:
                dados = json.load(f)
                # Atualiza o session_state com os dados do backup
                for k, v in dados.items():
                    if k not in st.session_state:
                        st.session_state[k] = v
            # Não mostramos toast aqui para não atrapalhar a UI inicial, mas os dados foram carregados.
        except:
            pass

# Função para Salvar Backup (Global)
def salvar_backup():
    try:
        # Filtra apenas dados primitivos do session_state (strings, ints, floats)
        # Ignora objetos complexos do Streamlit
        dados_para_salvar = {
            k: v for k, v in st.session_state.items() 
            if isinstance(v, (str, int, float, bool)) and not k.startswith("FormSubmiter")
        }
        with open(ARQUIVO_BACKUP, "w", encoding='utf-8') as f:
            json.dump(dados_para_salvar, f, indent=4, ensure_ascii=False)
    except:
        pass

# Executa o carregamento apenas uma vez na inicialização
if 'backup_carregado' not in st.session_state:
    carregar_backup()
    st.session_state.backup_carregado = True

# Inicialização de Variáveis de Controle
if 'form_key' not in st.session_state: st.session_state.form_key = 0

SECOES = [
    "1. Gerais", "2. Específicas", "3. Básicas", 
    "4. Profissionais", "5. Avançadas", "6. Reflexão"
]
if 'navegacao_atual' not in st.session_state: st.session_state.navegacao_atual = SECOES[0]

def obter_hora_ceara():
    fuso = timezone(timedelta(hours=-3))
    return datetime.now(fuso).strftime("%Y-%m-%d %H:%M:%S")

def limpar_formulario():
    """Reseta tudo e apaga o backup"""
    st.session_state.form_key += 1
    st.session_state.navegacao_atual = SECOES[0]
    # Limpa as chaves do session state relacionadas ao form antigo
    chaves_para_limpar = [k for k in st.session_state.keys() if k.startswith("nota_") or k.startswith("obs_") or k.startswith("novo_")]
    for k in chaves_para_limpar:
        del st.session_state[k]
        
    if os.path.exists(ARQUIVO_BACKUP):
        try: os.remove(ARQUIVO_BACKUP)
        except: pass

def navegar_proxima():
    try:
        idx = SECOES.index(st.session_state.navegacao_atual)
        if idx < len(SECOES) - 1:
            st.session_state.navegacao_atual = SECOES[idx + 1]
            salvar_backup() # Força salvamento ao mudar de aba
            st.rerun()
    except: pass

def renderizar_pergunta(texto_pergunta, id_unica, key_suffix=""):
    """Renderiza pergunta e já retorna o valor do session_state se existir."""
    # Gera chaves únicas baseadas no contador de formulário (reset)
    key_nota = f"nota_{id_unica}_{key_suffix}"
    key_obs = f"obs_{id_unica}_{key_suffix}"

    with st.container():
        st.markdown(f"""<div class="pergunta-card"><div class="pergunta-texto">{texto_pergunta}</div></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            val = st.select_slider(
                "Nível de Competência", 
                options=["N/A", "0", "1", "2", "3", "4", "5"], 
                value="N/A", 
                key=key_nota,
                help="Selecione 'N/A' se vazio."
            )
        with c2:
            obs = st.text_input(
                "Observações", 
                placeholder="Transcrição...", 
                key=key_obs
            )
    return val, obs

# ==============================================================================
# 4. CABEÇALHO
# ==============================================================================
st.markdown("""
    <div style="text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid rgba(128,128,128,0.2);">
        <h1 style="margin: 0; font-size: 2.5rem;">S.A.C.</h1>
        <div style="font-size: 1.2rem; font-weight: 600; opacity: 0.8;">SISTEMA DE AVALIAÇÃO CURRICULAR</div>
        <div style="font-size: 0.9rem; opacity: 0.6; margin-top: 5px;">PET ENGENHARIA QUÍMICA - UNIVERSIDADE FEDERAL DO CEARÁ</div>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. BARRA LATERAL
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ MODO DE OPERAÇÃO")
    modo_operacao = st.radio("Ação:", ["📝 Nova Transcrição", "✏️ Editar Registro", "📊 Painel Gerencial"], label_visibility="collapsed")
    st.markdown("---")

# ==============================================================================
# LÓGICA 1: NOVA TRANSCRIÇÃO (WIZARD)
# ==============================================================================
if modo_operacao == "📝 Nova Transcrição":
    st.sidebar.markdown("### 👤 IDENTIFICAÇÃO")
    
    # Chaves fixas para identificação (prefixo 'novo_')
    k_suffix = st.session_state.form_key
    
    lista_petianos = sorted(["", "Ana Carolina", "Ana Clara", "Ana Júlia", "Eric Rullian", "Gildelandio Junior", "Lucas Mossmann (trainee)", "Pedro Paulo"])
    petiano = st.sidebar.selectbox("Responsável", lista_petianos, key=f"novo_pet_{k_suffix}")
    nome = st.sidebar.text_input("Nome do Discente", key=f"novo_nome_{k_suffix}")
    matricula = st.sidebar.text_input("Matrícula", key=f"novo_mat_{k_suffix}")
    semestre = st.sidebar.selectbox("Semestre", [f"{i}º Semestre" for i in range(1, 11)], key=f"novo_sem_{k_suffix}")
    curriculo = st.sidebar.radio("Matriz", ["Novo (2023.1)", "Antigo (2005.1)"], key=f"novo_curr_{k_suffix}")
    
    # Botão de emergência para limpar rascunho
    if st.sidebar.button("🗑️ Descartar Rascunho"):
        limpar_formulario()
        st.rerun()

    # Navegação Superior
    secao_ativa = st.radio("Etapas:", SECOES, horizontal=True, key="navegacao_atual", label_visibility="collapsed")
    st.markdown("---")

    # Coleta de Respostas (Constrói dicionário dinâmico para salvar depois)
    # Como estamos salvando no session_state, só precisamos renderizar os widgets
    
    if secao_ativa == SECOES[0]: # Gerais
        st.markdown("### 1. COMPETÊNCIAS GERAIS")
        renderizar_pergunta("1. Projetar e conduzir experimentos", "q1", k_suffix)
        renderizar_pergunta("2. Desenvolver novas ferramentas", "q2", k_suffix)
        renderizar_pergunta("3. Conceber e projetar sistemas", "q3", k_suffix)
        renderizar_pergunta("4. Soluções para problemas de engenharia", "q4", k_suffix)
        renderizar_pergunta("5. Compreender fenômenos via modelos", "q5", k_suffix)
        renderizar_pergunta("6. Comunicação técnica", "q6", k_suffix)
        renderizar_pergunta("7. Trabalho em equipe", "q7", k_suffix)
        renderizar_pergunta("8. Ética profissional", "q8", k_suffix)
        
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav1")
            st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[1]: # Específicas
        st.markdown("### 2. COMPETÊNCIAS ESPECÍFICAS")
        renderizar_pergunta("9. Aplicar matemática/ciência", "q9", k_suffix)
        renderizar_pergunta("10. Modelar transf. de calor/massa", "q10", k_suffix)
        renderizar_pergunta("11. Aplicar FT em projetos", "q11", k_suffix)
        renderizar_pergunta("12. Mecanismos de transformação", "q12", k_suffix)
        renderizar_pergunta("13. Projetar separação/purificação", "q13", k_suffix)
        renderizar_pergunta("14. Cinética de reações", "q14", k_suffix)
        renderizar_pergunta("15. Projetar reatores", "q15", k_suffix)
        renderizar_pergunta("16. Controle de processos", "q16", k_suffix)
        renderizar_pergunta("17. Projetar plantas industriais", "q17", k_suffix)
        st.markdown("#### Eixos Práticos")
        renderizar_pergunta("18. Projeto básico e dimensionamento", "q18", k_suffix)
        renderizar_pergunta("19. Execução/Melhoria de processos", "q19", k_suffix)
        
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav2")
            st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[2]: # Básicas
        st.markdown("### 3. DISCIPLINAS BÁSICAS")
        with st.expander("CÁLCULO E FÍSICA", expanded=True):
            renderizar_pergunta("21. Cálculo: Analisar dados", "calc_21", k_suffix)
            renderizar_pergunta("52. Cálculo: Formação Básica", "calc_52", k_suffix)
            renderizar_pergunta("22. Física: Operação de sistemas", "fis_22", k_suffix)
            renderizar_pergunta("53. Física: Ciência da Engenharia", "fis_53", k_suffix)
        with st.expander("QUÍMICA E TERMO", expanded=True):
            renderizar_pergunta("23. Química: Conhecimentos de transf.", "qui_23", k_suffix)
            renderizar_pergunta("24. Química: Conceber produtos", "qui_24", k_suffix)
            renderizar_pergunta("25. Termo: Sistemas energéticos", "termo_25", k_suffix)
            renderizar_pergunta("54. Termo: Ciência da EQ", "termo_54", k_suffix)
        with st.expander("FENÔMENOS", expanded=True):
            renderizar_pergunta("26. FT: Aplicar conhecimentos", "ft_26", k_suffix)
            renderizar_pergunta("27. FT: Comunicação gráfica", "ft_27", k_suffix)
            renderizar_pergunta("28. MecFlu: Implantar soluções", "mecflu_28", k_suffix)
            renderizar_pergunta("29. MecFlu: Supervisionar", "mecflu_29", k_suffix)
        
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav3")
            st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[3]: # Profissionais
        st.markdown("### 4. DISCIPLINAS PROFISSIONAIS")
        with st.expander("OPERAÇÕES UNITÁRIAS", expanded=True):
            renderizar_pergunta("30. Inspecionar manutenção", "op1_30", k_suffix)
            renderizar_pergunta("55. Tecnologia Industrial", "op1_55", k_suffix)
            renderizar_pergunta("31. Estudos ambientais", "op2_31", k_suffix)
            renderizar_pergunta("32. Tratamento ambiental", "op2_32", k_suffix)
        with st.expander("REATORES E CONTROLE", expanded=True):
            renderizar_pergunta("33. Gerir recursos", "reat_33", k_suffix)
            renderizar_pergunta("34. Controle de qualidade", "reat_34", k_suffix)
            renderizar_pergunta("35. Controle: Supervisão", "ctrl_35", k_suffix)
            renderizar_pergunta("36. Gestão de empreendimentos", "ctrl_36", k_suffix)
        with st.expander("PROJETOS", expanded=True):
            renderizar_pergunta("56. Gestão Industrial", "proj_56", k_suffix)
            renderizar_pergunta("57. Ética e Humanidades", "proj_57", k_suffix)
        
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav4")
            st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[4]: # Avançadas
        st.markdown("### 5. AVANÇADAS E COMPLEMENTARES")
        with st.expander("GESTÃO/AMBIENTAL", expanded=True):
            renderizar_pergunta("37. Eng. Econ: Novos conceitos", "econ_37", k_suffix)
            renderizar_pergunta("38. Eng. Econ: Visão global", "econ_38", k_suffix)
            renderizar_pergunta("39. Gestão: Comprometimento", "gest_39", k_suffix)
            renderizar_pergunta("40. Gestão: Resultados", "gest_40", k_suffix)
            renderizar_pergunta("41. Ambiental: Inovação", "amb_41", k_suffix)
            renderizar_pergunta("42. Ambiental: Novas situações", "amb_42", k_suffix)
            renderizar_pergunta("43. Segurança: Incertezas", "seg_43", k_suffix)
            renderizar_pergunta("44. Segurança: Decisão", "seg_44", k_suffix)
        with st.expander("PRÁTICAS", expanded=True):
            renderizar_pergunta("45. Lab: Criatividade", "lab_45", k_suffix)
            renderizar_pergunta("46. Lab: Relacionamento", "lab_46", k_suffix)
            renderizar_pergunta("47. Estágio: Autocontrole", "est_47", k_suffix)
            renderizar_pergunta("48. Estágio: Empreendedorismo", "est_48", k_suffix)
        with st.expander("OPTATIVAS E INTEGRADORAS", expanded=True):
            renderizar_pergunta("49. Biotec: Dados", "bio_49", k_suffix)
            renderizar_pergunta("50. Biotec: Ferramentas", "bio_50", k_suffix)
            renderizar_pergunta("51. Petróleo: Recuperação", "petro_51", k_suffix)
            renderizar_pergunta("52. Petróleo: Reatores", "petro_52", k_suffix)
            renderizar_pergunta("57. Simulação: Dados", "sim_57", k_suffix)
            renderizar_pergunta("58. Simulação: Comunicação", "sim_58", k_suffix)
            renderizar_pergunta("59. Otimização: Soluções", "otim_59", k_suffix)
            renderizar_pergunta("60. Otimização: Modelos", "otim_60", k_suffix)
            renderizar_pergunta("61. TCC: Comunicação", "tcc_61", k_suffix)
            renderizar_pergunta("62. TCC: Liderança", "tcc_62", k_suffix)
        
        col1, col2 = st.columns([0.8, 0.2])
        with col2: 
            st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
            st.button("AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav5")
            st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[5]: # Reflexão (Final)
        st.markdown("### 6. REFLEXÃO FINAL E AUTOAVALIAÇÃO")
        st.warning("⚠️ **ATENÇÃO:** O preenchimento desta seção é OBRIGATÓRIO para salvar.")
        
        renderizar_pergunta("20. Capacidade de aprender novos conceitos", "q20_indiv", k_suffix)
        
        st.markdown("#### TRANSCRIÇÃO DAS RESPOSTAS ABERTAS")
        
        # Campos de texto direto
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
            # Consolida dados do session_state em um dicionário limpo
            # Recupera dados usando as chaves conhecidas
            dados_para_salvar = {}
            
            # Dados de Identificação
            dados_para_salvar["Petiano_Responsavel"] = st.session_state[f"novo_pet_{k_suffix}"]
            dados_para_salvar["Nome"] = st.session_state[f"novo_nome_{k_suffix}"]
            dados_para_salvar["Matricula"] = st.session_state[f"novo_mat_{k_suffix}"]
            dados_para_salvar["Semestre"] = st.session_state[f"novo_sem_{k_suffix}"]
            dados_para_salvar["Curriculo"] = st.session_state[f"novo_curr_{k_suffix}"]
            dados_para_salvar["Data_Registro"] = obter_hora_ceara()
            
            # Textos Finais
            dados_para_salvar["Autoavaliação: Pontos Fortes"] = txt_fortes
            dados_para_salvar["Autoavaliação: Pontos a Desenvolver"] = txt_fracos
            dados_para_salvar["Contribuição Prática"] = txt_prat
            dados_para_salvar["Exemplos de Aplicação"] = txt_ex
            dados_para_salvar["Competências Futuras"] = txt_fut1
            dados_para_salvar["Plano de Desenvolvimento"] = txt_fut2
            dados_para_salvar["Observações Finais"] = txt_obs
            
            # Captura todas as notas e obs de sliders do session_state
            for k, v in st.session_state.items():
                if f"_{k_suffix}" in k: # Só pega dados da sessão atual
                    if k.startswith("nota_"):
                        nome_coluna = k.replace("nota_", "").replace(f"_{k_suffix}", "")
                        dados_para_salvar[nome_coluna] = v
                    elif k.startswith("obs_"):
                        nome_coluna = k.replace("obs_", "Obs_").replace(f"_{k_suffix}", "")
                        dados_para_salvar[nome_coluna] = v

            # Validação
            erros = []
            if not dados_para_salvar["Nome"]: erros.append("Nome do Discente")
            if not dados_para_salvar["Petiano_Responsavel"]: erros.append("Responsável")
            if not dados_para_salvar["Autoavaliação: Pontos Fortes"] or not dados_para_salvar["Autoavaliação: Pontos a Desenvolver"]:
                erros.append("Campos de Reflexão Final (Digite 'EM BRANCO' se vazio)")

            if erros:
                st.error(f"❌ AÇÃO BLOQUEADA. Preencha: {', '.join(erros)}")
            else:
                try:
                    df_new = pd.DataFrame([dados_para_salvar])
                    if os.path.exists(ARQUIVO_DB):
                        df_new.to_csv(ARQUIVO_DB, mode='a', header=False, index=False)
                    else:
                        df_new.to_csv(ARQUIVO_DB, mode='w', header=True, index=False)
                    
                    st.balloons()
                    st.success(f"✅ Transcrição de {dados_para_salvar['Nome']} salva com sucesso!")
                    limpar_formulario()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Aciona o Auto-Save a cada renderização do modo Nova Transcrição
    salvar_backup()

# ==============================================================================
# LÓGICA 2: MODO DE EDIÇÃO
# ==============================================================================
elif modo_operacao == "✏️ Editar Registro":
    st.markdown("### ✏️ MODO DE EDIÇÃO DE REGISTROS")
    st.info("Utilize esta aba para corrigir erros de digitação em formulários já salvos.")
    
    if not os.path.exists(ARQUIVO_DB):
        st.warning("Ainda não há dados salvos para editar.")
    else:
        try:
            df = pd.read_csv(ARQUIVO_DB, dtype=str) # Lê tudo como texto
            if df.empty:
                st.warning("Banco de dados vazio.")
            else:
                # Seleção do Aluno
                opcoes_alunos = df.apply(lambda x: f"{x.name} | {x['Nome']} ({x['Matricula']})", axis=1)
                aluno_selecionado = st.selectbox("Selecione o Registro para Editar:", opcoes_alunos)
                index_aluno = int(aluno_selecionado.split(" | ")[0])
                
                # Carrega dados da linha selecionada
                dados_aluno = df.iloc[index_aluno]
                
                st.markdown("---")
                
                # Edição dos Campos Principais
                with st.form("form_edicao"):
                    st.subheader("Dados Cadastrais")
                    c1, c2 = st.columns(2)
                    novo_nome = c1.text_input("Nome", value=dados_aluno["Nome"])
                    nova_mat = c2.text_input("Matrícula", value=dados_aluno["Matricula"])
                    
                    st.subheader("Alteração Rápida de Notas")
                    st.caption("Abaixo estão listadas todas as colunas de notas encontradas.")
                    
                    # Dicionário para guardar as edições
                    edicoes = {}
                    
                    # Filtra colunas de notas (Exclui dados fixos e obs)
                    cols_ignorar = ['Nome', 'Matricula', 'Semestre', 'Curriculo', 'Data_Registro', 'Petiano_Responsavel']
                    cols_notas = [c for c in df.columns if c not in cols_ignorar and not c.startswith("Obs") and not c.startswith("Auto") and not c.startswith("Contribuição") and not c.startswith("Exemplos") and not c.startswith("Competências") and not c.startswith("Plano") and not c.startswith("Comentários") and not c.startswith("Justificativa")]
                    
                    # Mostra sliders para edição
                    for col in cols_notas:
                        valor_atual = dados_aluno[col] if col in dados_aluno else "N/A"
                        # Garante que o valor está nas opções
                        if valor_atual not in ["N/A", "0", "1", "2", "3", "4", "5"]:
                            valor_atual = "N/A"
                            
                        novo_val = st.select_slider(
                            f"{col}", 
                            options=["N/A", "0", "1", "2", "3", "4", "5"], 
                            value=valor_atual,
                            key=f"edit_{col}"
                        )
                        edicoes[col] = novo_val

                    st.markdown("---")
                    if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        # Atualiza o DataFrame na memória
                        df.at[index_aluno, "Nome"] = novo_nome
                        df.at[index_aluno, "Matricula"] = nova_mat
                        for k, v in edicoes.items():
                            df.at[index_aluno, k] = v
                        
                        # Salva no disco
                        df.to_csv(ARQUIVO_DB, index=False)
                        st.success("Registro atualizado com sucesso!")
                        st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar edição: {e}")

# ==============================================================================
# LÓGICA 3: PAINEL GERENCIAL (COM FILTROS)
# ==============================================================================
elif modo_operacao == "📊 Painel Gerencial":
    st.markdown("### 📊 INDICADORES DE DESEMPENHO")
    
    if os.path.exists(ARQUIVO_DB):
        try:
            df = pd.read_csv(ARQUIVO_DB, dtype={'Matricula': str})
            
            # FILTRO POR PETIANO
            petianos_unicos = sorted(list(df['Petiano_Responsavel'].unique()))
            lista_responsaveis = ["Todos"] + petianos_unicos
            filtro_resp = st.selectbox("Filtrar por Responsável:", lista_responsaveis)
            
            if filtro_resp != "Todos":
                df_view = df[df['Petiano_Responsavel'] == filtro_resp]
            else:
                df_view = df
            
            st.markdown("---")
            
            # KPIs
            c1, c2, c3 = st.columns(3)
            c1.metric("Formulários (Filtro)", len(df_view))
            
            # Cálculo de Média (Ignorando N/A e Textos)
            cols_ignorar = ['Nome', 'Matricula', 'Semestre', 'Curriculo', 'Data_Registro', 'Petiano_Responsavel']
            cols_calc = [c for c in df_view.columns if c not in cols_ignorar and not c.startswith("Obs") and not c.startswith("Auto") and not c.startswith("Contribuição") and not c.startswith("Exemplos") and not c.startswith("Competências") and not c.startswith("Plano") and not c.startswith("Comentários") and not c.startswith("Justificativa")]
            
            # Converte para numérico (N/A vira NaN)
            df_numeric = df_view[cols_calc].apply(pd.to_numeric, errors='coerce')
            
            if not df_numeric.empty:
                media = df_numeric.mean().mean()
                c2.metric("Média de Competências", f"{media:.2f}/5.0")
            
            if not df_view.empty:
                last = pd.to_datetime(df_view['Data_Registro']).max()
                c3.metric("Última Atividade", last.strftime("%d/%m %H:%M"))
            
            st.markdown("#### Detalhamento dos Dados")
            st.dataframe(df_view, use_container_width=True, height=500)
            
            csv = df_view.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Relatório (Excel)", csv, "sac_relatorio.csv", "text/csv")
            
        except Exception as e:
            st.error(f"Erro ao ler dados: {e}")
    else:
        st.info("Nenhum dado registrado.")
