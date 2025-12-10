import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
from datetime import datetime, timedelta, timezone

# ==============================================================================
# 1. CONFIGURAÇÕES GERAIS
# ==============================================================================
st.set_page_config(
    page_title="S.A.C. - PET Engenharia Química", 
    layout="wide", 
    page_icon="📊", 
    initial_sidebar_state="expanded"
)

ARQUIVO_DB = "respostas_sac_deq.csv"
ARQUIVO_BACKUP = "_backup_autosave.json"

# ==============================================================================
# 2. ESTILO VISUAL (CSS AVANÇADO)
# ==============================================================================
st.markdown("""
    <style>
    :root { --primary: #002060; --secondary: #dba800; }
    .stApp { font-family: 'Segoe UI', sans-serif; }
    
    /* Títulos */
    h1, h2, h3, h4 { color: var(--primary) !important; font-weight: 800 !important; text-transform: uppercase; }
    
    /* Cards de Perguntas */
    .pergunta-card {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(0,0,0,0.1);
        border-left: 5px solid var(--primary);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .pergunta-texto { font-weight: 700; font-size: 1.1rem; margin-bottom: 10px; opacity: 0.9; }

    /* Botões */
    .stButton button { border-radius: 6px; font-weight: bold; text-transform: uppercase; height: 3.5em; width: 100%; }
    .botao-avancar button { border: 2px solid var(--primary); color: var(--primary); background: transparent; }
    .botao-avancar button:hover { background: var(--primary); color: white; }
    .botao-final button { background: var(--primary) !important; color: white !important; border: none; }

    /* Métricas do Dashboard */
    div[data-testid="stMetric"] {
        background-color: rgba(0, 32, 96, 0.05);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid rgba(0, 32, 96, 0.1);
    }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CABEÇALHO
# ==============================================================================
st.markdown("""
    <div style="text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid rgba(128,128,128,0.2);">
        <h1 style="margin: 0; font-size: 2.5rem;">S.A.C.</h1>
        <div style="font-size: 1.2rem; font-weight: 600; opacity: 0.8;">SISTEMA DE AVALIAÇÃO CURRICULAR</div>
        <div style="font-size: 0.9rem; opacity: 0.6; margin-top: 5px;">PET ENGENHARIA QUÍMICA - UFC</div>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. FUNÇÕES AUXILIARES
# ==============================================================================
SECOES = ["1. Gerais", "2. Específicas", "3. Básicas", "4. Profissionais", "5. Avançadas", "6. Reflexão"]

# Listas de Referência
LISTA_PETIANOS = sorted(["", "Ana Carolina", "Ana Clara", "Ana Júlia", "Eric Rullian", "Gildelandio Junior", "Lucas Mossmann (trainee)", "Pedro Paulo"])
LISTA_SEMESTRES = [f"{i}º Semestre" for i in range(1, 11)]
LISTA_CURRICULOS = ["Novo (2023.1)", "Antigo (2005.1)", "Troca de Matriz"]

# Inicialização de Estado
if 'form_key' not in st.session_state: st.session_state.form_key = 0
if 'navegacao_atual' not in st.session_state: st.session_state.navegacao_atual = SECOES[0]

def obter_hora_ceara():
    return datetime.now(timezone(timedelta(hours=-3))).strftime("%Y-%m-%d %H:%M:%S")

def limpar_formulario():
    st.session_state.form_key += 1
    st.session_state.navegacao_atual = SECOES[0]
    if os.path.exists(ARQUIVO_BACKUP):
        try: os.remove(ARQUIVO_BACKUP)
        except: pass

def renderizar_pergunta(texto, id_unica, valor="N/A", obs="", k_sfx=""):
    k = k_sfx if k_sfx else f"_{st.session_state.form_key}"
    with st.container():
        st.markdown(f"""<div class="pergunta-card"><div class="pergunta-texto">{texto}</div></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns([0.5, 0.5])
        with c1:
            val = st.select_slider("Nota", options=["N/A", "0", "1", "2", "3", "4", "5"], value=str(valor), key=f"nota_{id_unica}{k}")
        with c2:
            o = st.text_input("Obs.", value=str(obs) if pd.notna(obs) else "", key=f"obs_{id_unica}{k}")
    return val, o

# ==============================================================================
# 5. BARRA LATERAL
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ MODO DE OPERAÇÃO")
    modo = st.radio("Ação:", ["📝 Nova Transcrição", "✏️ Editar Registro", "📊 Painel Gerencial"], label_visibility="collapsed")
    st.markdown("---")

    if modo == "📝 Nova Transcrição":
        tab1, tab2 = st.tabs(["Identificação", "Ajuda"])
        with tab1:
            k = f"_{st.session_state.form_key}"
            st.session_state[f"pet_{k}"] = st.selectbox("Responsável", LISTA_PETIANOS, key=f"wid_pet{k}")
            st.session_state[f"nome_{k}"] = st.text_input("Nome Discente", key=f"wid_nome{k}")
            st.session_state[f"mat_{k}"] = st.text_input("Matrícula", key=f"wid_mat{k}")
            st.session_state[f"sem_{k}"] = st.selectbox("Semestre", LISTA_SEMESTRES, key=f"wid_sem{k}")
            st.session_state[f"curr_{k}"] = st.radio("Matriz", LISTA_CURRICULOS, key=f"wid_curr{k}")
            
            if st.button("🗑️ Limpar"): limpar_formulario(); st.rerun()

        with tab2:
            st.info("**N/A:** Use para branco/rasurado.\n**0-5:** Notas.\n**Texto:** Transcreva ipsis litteris.")

# ==============================================================================
# LÓGICA 1: WIZARD DE TRANSCRIÇÃO
# ==============================================================================
if modo == "📝 Nova Transcrição":
    secao = st.radio("Etapas:", SECOES, horizontal=True, key="navegacao_atual", label_visibility="collapsed")
    st.markdown("---")
    k = f"_{st.session_state.form_key}"

    if secao == SECOES[0]: # Gerais
        st.markdown("### 1. COMPETÊNCIAS GERAIS")
        renderizar_pergunta("1. Projetar e conduzir experimentos", "q1", k_sfx=k)
        renderizar_pergunta("2. Desenvolver novas ferramentas", "q2", k_sfx=k)
        renderizar_pergunta("3. Conceber e projetar sistemas", "q3", k_sfx=k)
        renderizar_pergunta("4. Resolução de problemas", "q4", k_sfx=k)
        renderizar_pergunta("5. Modelagem de fenômenos", "q5", k_sfx=k)
        renderizar_pergunta("6. Comunicação técnica", "q6", k_sfx=k)
        renderizar_pergunta("7. Trabalho em equipe", "q7", k_sfx=k)
        renderizar_pergunta("8. Ética profissional", "q8", k_sfx=k)
        
        st.markdown("---")
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        if st.button("AVANÇAR ➡️", key="nav1"): 
            st.session_state.navegacao_atual = SECOES[1]; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif secao == SECOES[1]: # Específicas
        st.markdown("### 2. COMPETÊNCIAS ESPECÍFICAS")
        renderizar_pergunta("9. Fundamentos matemáticos", "q9", k_sfx=k)
        renderizar_pergunta("10. Modelagem de transporte", "q10", k_sfx=k)
        renderizar_pergunta("11. Aplicar transporte", "q11", k_sfx=k)
        renderizar_pergunta("12. Transf. matéria/energia", "q12", k_sfx=k)
        renderizar_pergunta("13. Separação e purificação", "q13", k_sfx=k)
        renderizar_pergunta("14. Cinética química", "q14", k_sfx=k)
        renderizar_pergunta("15. Reatores químicos", "q15", k_sfx=k)
        renderizar_pergunta("16. Controle de processos", "q16", k_sfx=k)
        renderizar_pergunta("17. Projetos industriais", "q17", k_sfx=k)
        st.markdown("#### Eixos Práticos")
        renderizar_pergunta("18. Projeto básico", "q18", k_sfx=k)
        renderizar_pergunta("19. Melhoria de processos", "q19", k_sfx=k)

        st.markdown("---")
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        if st.button("AVANÇAR ➡️", key="nav2"): 
            st.session_state.navegacao_atual = SECOES[2]; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif secao == SECOES[2]: # Básicas
        st.markdown("### 3. DISCIPLINAS BÁSICAS")
        with st.expander("CÁLCULO E FÍSICA", expanded=True):
            renderizar_pergunta("21. Cálculo: Análise dados", "calc_21", k_sfx=k)
            renderizar_pergunta("52. Cálculo: Formação", "calc_52", k_sfx=k)
            renderizar_pergunta("22. Física: Operação", "fis_22", k_sfx=k)
            renderizar_pergunta("53. Física: Ciência", "fis_53", k_sfx=k)
        with st.expander("QUÍMICA E TERMO", expanded=True):
            renderizar_pergunta("23. Química: Transformação", "qui_23", k_sfx=k)
            renderizar_pergunta("24. Química: Produtos", "qui_24", k_sfx=k)
            renderizar_pergunta("25. Termo: Energia", "termo_25", k_sfx=k)
            renderizar_pergunta("54. Termo: Ciência", "termo_54", k_sfx=k)
        with st.expander("FENÔMENOS", expanded=True):
            renderizar_pergunta("26. FT: Aplicação", "ft_26", k_sfx=k)
            renderizar_pergunta("27. FT: Comunicação", "ft_27", k_sfx=k)
            renderizar_pergunta("28. MecFlu: Soluções", "mecflu_28", k_sfx=k)
            renderizar_pergunta("29. MecFlu: Supervisão", "mecflu_29", k_sfx=k)

        st.markdown("---")
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        if st.button("AVANÇAR ➡️", key="nav3"): 
            st.session_state.navegacao_atual = SECOES[3]; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif secao == SECOES[3]: # Profissionais
        st.markdown("### 4. DISCIPLINAS PROFISSIONAIS")
        with st.expander("OPERAÇÕES E REATORES", expanded=True):
            renderizar_pergunta("30. OpUnit: Manutenção", "op1_30", k_sfx=k)
            renderizar_pergunta("55. OpUnit: Tecnologia", "op1_55", k_sfx=k)
            renderizar_pergunta("31. OpUnit: Ambiental", "op2_31", k_sfx=k)
            renderizar_pergunta("32. OpUnit: Tratamento", "op2_32", k_sfx=k)
            renderizar_pergunta("33. Reatores: Recursos", "reat_33", k_sfx=k)
            renderizar_pergunta("34. Reatores: Qualidade", "reat_34", k_sfx=k)
        with st.expander("CONTROLE E PROJETOS", expanded=True):
            renderizar_pergunta("35. Controle: Supervisão", "ctrl_35", k_sfx=k)
            renderizar_pergunta("36. Controle: Gestão", "ctrl_36", k_sfx=k)
            renderizar_pergunta("56. Projetos: Gestão", "proj_56", k_sfx=k)
            renderizar_pergunta("57. Projetos: Ética", "proj_57", k_sfx=k)

        st.markdown("---")
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        if st.button("AVANÇAR ➡️", key="nav4"): 
            st.session_state.navegacao_atual = SECOES[4]; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif secao == SECOES[4]: # Avançadas
        st.markdown("### 5. AVANÇADAS")
        with st.expander("GESTÃO E AMBIENTAL", expanded=True):
            renderizar_pergunta("37. Econômica: Novos conceitos", "econ_37", k_sfx=k)
            renderizar_pergunta("38. Econômica: Visão global", "econ_38", k_sfx=k)
            renderizar_pergunta("39. Gestão: Comprometimento", "gest_39", k_sfx=k)
            renderizar_pergunta("40. Gestão: Resultados", "gest_40", k_sfx=k)
            renderizar_pergunta("41. Ambiental: Inovação", "amb_41", k_sfx=k)
            renderizar_pergunta("42. Ambiental: Situações", "amb_42", k_sfx=k)
            renderizar_pergunta("43. Segurança: Incertezas", "seg_43", k_sfx=k)
            renderizar_pergunta("44. Segurança: Decisão", "seg_44", k_sfx=k)
        with st.expander("PRÁTICAS E OPTATIVAS", expanded=True):
            renderizar_pergunta("45. Lab: Criatividade", "lab_45", k_sfx=k)
            renderizar_pergunta("46. Lab: Relacionamento", "lab_46", k_sfx=k)
            renderizar_pergunta("47. Estágio: Autocontrole", "est_47", k_sfx=k)
            renderizar_pergunta("48. Estágio: Empreendedorismo", "est_48", k_sfx=k)
            renderizar_pergunta("49. Biotec: Dados", "bio_49", k_sfx=k)
            renderizar_pergunta("50. Biotec: Ferramentas", "bio_50", k_sfx=k)
            renderizar_pergunta("51. Petróleo: Recuperação", "petro_51", k_sfx=k)
            renderizar_pergunta("52. Petróleo: Reatores", "petro_52", k_sfx=k)
            renderizar_pergunta("57. Simulação: Dados", "sim_57", k_sfx=k)
            renderizar_pergunta("58. Simulação: Comunicação", "sim_58", k_sfx=k)
            renderizar_pergunta("59. Otimização: Soluções", "otim_59", k_sfx=k)
            renderizar_pergunta("60. Otimização: Modelos", "otim_60", k_sfx=k)
            renderizar_pergunta("61. TCC: Comunicação", "tcc_61", k_sfx=k)
            renderizar_pergunta("62. TCC: Liderança", "tcc_62", k_sfx=k)

        st.markdown("---")
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        if st.button("AVANÇAR ➡️", key="nav5"): 
            st.session_state.navegacao_atual = SECOES[5]; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif secao == SECOES[5]: # Final
        st.markdown("### 6. REFLEXÃO FINAL (OBRIGATÓRIA)")
        st.warning("Se o aluno deixou em branco, digite 'EM BRANCO'.")
        
        renderizar_pergunta("20. Capacidade de aprendizado ágil", "q20_indiv", k_sfx=k)
        
        st.markdown("#### Respostas Abertas")
        txt_fortes = st.text_area("Pontos Fortes", key=f"txt_fortes{k}")
        txt_fracos = st.text_area("Pontos a Desenvolver", key=f"txt_fracos{k}")
        txt_prat = st.text_area("Contribuição Prática", key=f"txt_prat{k}")
        txt_ex = st.text_area("Exemplos", key=f"txt_ex{k}")
        txt_fut1 = st.text_area("Competências Futuras", key=f"txt_fut1{k}")
        txt_fut2 = st.text_area("Plano Desenv.", key=f"txt_fut2{k}")
        txt_obs = st.text_area("Comentários Finais", key=f"txt_obs{k}")

        st.markdown("---")
        st.markdown('<div class="botao-final">', unsafe_allow_html=True)
        
        if st.button("💾 FINALIZAR REGISTRO"):
            # Validação
            nome = st.session_state.get(f"wid_nome{k}", "")
            pet = st.session_state.get(f"wid_pet{k}", "")
            
            if not nome or not pet:
                st.error("❌ ERRO: Preencha Nome e Responsável na barra lateral.")
            elif not txt_fortes or not txt_fracos:
                st.error("❌ ERRO: 'Pontos Fortes' e 'Pontos a Desenvolver' são obrigatórios.")
            else:
                try:
                    # Coleta dados
                    dados = {
                        "Petiano_Responsavel": pet,
                        "Nome": nome,
                        "Matricula": st.session_state.get(f"wid_mat{k}", ""),
                        "Semestre": st.session_state.get(f"wid_sem{k}", ""),
                        "Curriculo": st.session_state.get(f"wid_curr{k}", ""),
                        "Data_Registro": obter_hora_ceara(),
                        "Autoavaliação_Fortes": txt_fortes,
                        "Autoavaliação_Fracos": txt_fracos,
                        "Pratica": txt_prat, "Exemplos": txt_ex,
                        "Futuro": txt_fut1, "Plano": txt_fut2, "Obs_Final": txt_obs
                    }
                    
                    # Varre session state por notas e obs
                    for key, val in st.session_state.items():
                        if key.endswith(k):
                            if key.startswith("nota_"): dados[key.replace("nota_", "").replace(k, "")] = val
                            elif key.startswith("obs_"): dados["Obs_" + key.replace("obs_", "").replace(k, "")] = val

                    df_new = pd.DataFrame([dados])
                    
                    # Salva (com tratamento para arquivo corrompido)
                    if os.path.exists(ARQUIVO_DB):
                        try:
                            df_old = pd.read_csv(ARQUIVO_DB, dtype=str)
                            df_final = pd.concat([df_old, df_new], ignore_index=True)
                            df_final.to_csv(ARQUIVO_DB, index=False)
                        except:
                            df_new.to_csv(ARQUIVO_DB, index=False)
                    else:
                        df_new.to_csv(ARQUIVO_DB, index=False)
                    
                    st.balloons()
                    st.success(f"Registro de {nome} salvo!")
                    limpar_formulario()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-save simples
    try:
        if 'wid_nome'+k in st.session_state:
            with open(ARQUIVO_BACKUP, 'w') as f:
                json.dump({key: val for key, val in st.session_state.items() if isinstance(val, (str, int, float, bool))}, f)
    except: pass

# ==============================================================================
# LÓGICA 2: EDIÇÃO
# ==============================================================================
elif modo == "✏️ Editar Registro":
    st.markdown("### ✏️ EDIÇÃO DE REGISTROS")
    if not os.path.exists(ARQUIVO_DB):
        st.warning("Sem dados.")
    else:
        try:
            df = pd.read_csv(ARQUIVO_DB, dtype=str)
            opcoes = df.apply(lambda x: f"{x.name} | {x['Nome']}", axis=1)
            sel = st.selectbox("Selecione:", opcoes)
            idx = int(sel.split(" | ")[0])
            d = df.iloc[idx]

            with st.form("editor"):
                c1, c2 = st.columns(2)
                nm = c1.text_input("Nome", d.get("Nome", ""))
                mt = c2.text_input("Matrícula", d.get("Matricula", ""))
                
                # Campos de nota
                cols_nota = [c for c in df.columns if c not in ['Nome', 'Matricula', 'Data_Registro', 'Semestre', 'Curriculo', 'Petiano_Responsavel'] and not c.startswith("Obs") and not c.startswith("Auto") and not c.startswith("Pratica")]
                
                col_edit = st.selectbox("Competência para editar:", cols_notas)
                val_atual = d.get(col_edit, "N/A")
                if val_atual not in ["0","1","2","3","4","5","N/A"]: val_atual="N/A"
                
                new_val = st.select_slider(f"Nova Nota: {col_edit}", ["N/A","0","1","2","3","4","5"], value=val_atual)
                
                if st.form_submit_button("Salvar"):
                    df.at[idx, "Nome"] = nm
                    df.at[idx, "Matricula"] = mt
                    df.at[idx, col_edit] = new_val
                    df.to_csv(ARQUIVO_DB, index=False)
                    st.success("Atualizado!")
                    st.rerun()
        except: st.error("Erro ao carregar.")

# ==============================================================================
# LÓGICA 3: PAINEL GERENCIAL (AVANÇADO)
# ==============================================================================
elif modo == "📊 Painel Gerencial":
    st.markdown("### 📊 DASHBOARD ANALÍTICO")
    
    if os.path.exists(ARQUIVO_DB):
        try:
            df = pd.read_csv(ARQUIVO_DB, dtype=str) # Lê tudo como string para segurança
            
            # --- FILTROS ---
            c_f1, c_f2 = st.columns(2)
            sems = sorted(list(df['Semestre'].dropna().unique()))
            f_sem = c_f1.selectbox("Filtrar Semestre:", ["Todos"] + sems)
            
            currs = sorted(list(df['Curriculo'].dropna().unique()))
            f_curr = c_f2.selectbox("Filtrar Matriz:", ["Todos"] + currs)
            
            df_show = df.copy()
            if f_sem != "Todos": df_show = df_show[df_show['Semestre'] == f_sem]
            if f_curr != "Todos": df_show = df_show[df_show['Curriculo'] == f_curr]
            
            # --- PROCESSAMENTO DE DADOS ---
            # Identifica colunas de nota (excluindo textos e identificação)
            cols_ignorar = ['Nome', 'Matricula', 'Semestre', 'Curriculo', 'Data_Registro', 'Petiano_Responsavel']
            cols_notas = [c for c in df.columns if c not in cols_ignorar and not c.startswith("Obs") and not c.startswith("Auto") and not c.startswith("Pratica") and not c.startswith("Exemplos") and not c.startswith("Futuro") and not c.startswith("Plano")]
            
            # Converte para numérico (N/A vira NaN)
            df_nums = df_show[cols_notas].apply(pd.to_numeric, errors='coerce')
            
            # ABAS DO DASHBOARD
            tab_kpi, tab_dist, tab_text, tab_data = st.tabs(["📈 Visão Geral", "📊 Distribuição", "💬 Comentários", "📋 Dados Brutos"])
            
            with tab_kpi:
                c1, c2, c3 = st.columns(3)
                c1.metric("Formulários", len(df_show))
                
                if not df_nums.empty:
                    media_geral = df_nums.stack().mean()
                    std_geral = df_nums.stack().std()
                    c2.metric("Média Global", f"{media_geral:.2f}/5.0")
                    c3.metric("Desvio Padrão", f"{std_geral:.2f}")
                    
                    st.markdown("#### Ranking de Competências")
                    medias = df_nums.mean().sort_values(ascending=True)
                    fig = px.bar(medias, orientation='h', x=medias.values, y=medias.index, text_auto='.2f',
                                 labels={'index': '', 'x': 'Média'},
                                 color=medias.values,
                                 color_continuous_scale=[(0, '#cfd8dc'), (0.5, '#dba800'), (1, '#002060')])
                    fig.update_layout(height=800, plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Sem dados numéricos suficientes.")

            with tab_dist:
                st.markdown("#### Dispersão das Notas (Boxplot)")
                if not df_nums.empty:
                    fig_box = px.box(df_nums, orientation='h')
                    fig_box.update_layout(height=800, plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_box, use_container_width=True)
            
            with tab_text:
                st.markdown("#### Explorador de Textos")
                col_txt = st.selectbox("Selecione o campo de texto:", [c for c in df_show.columns if c.startswith("Obs") or c.startswith("Auto")])
                for i, row in df_show.iterrows():
                    txt = row[col_txt]
                    if pd.notna(txt) and len(str(txt)) > 2:
                        with st.expander(f"{row['Nome']} ({row['Semestre']})"):
                            st.write(txt)
            
            with tab_data:
                st.dataframe(df_show, use_container_width=True)
                csv = df_show.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Baixar CSV", csv, "relatorio_sac.csv", "text/csv")
                
        except Exception as e: st.error(f"Erro ao processar dados: {e}")
    else:
        st.info("Nenhum dado registrado.")
