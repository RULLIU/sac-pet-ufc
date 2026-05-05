# app.py / sac.py
import os
import json
import uuid
import time
from datetime import datetime, timedelta, timezone
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Importações dos módulos 
from config import SECOES, LISTA_PETIANOS, LISTA_SEMESTRES, LISTA_CURRICULOS, NOTA_LABELS, ORDEM_QUESTOES, ID_PARA_LABEL, ID_PARA_TEXTO
from database import ler_banco_cacheados, inserir_registro, atualizar_registro

# ==============================================================================
# CONFIGURAÇÕES E ESTILO
# ==============================================================================
st.set_page_config(page_title="S.A.C. - PET Engenharia Química", layout="wide", page_icon="📝")

st.markdown("""
<style>
:root { --primary-color: #002060; }
.pergunta-card { background-color: #ffffff; border-radius: 8px; padding: 16px 24px; margin-bottom: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); border-left: 6px solid #002060; border: 1px solid #edf2f7; }
.pergunta-texto { font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; color: #1e1e1e; }
div[role="radiogroup"] { flex-direction: row; gap: 15px; } 
.edit-warning { padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; background-color: #fff3e0; color: #e65100; }
.header-box { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
.login-box { max-width: 400px; margin: 0 auto; padding: 30px; border: 1px solid #e9ecef; border-radius: 10px; background-color: #f8f9fa; text-align: center; }
.kpi-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #f0f2f6; text-align: center; }
.kpi-valor { font-size: 2rem; font-weight: 800; color: #002060; margin: 0; }
.kpi-titulo { font-size: 0.9rem; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
#MainMenu{visibility:hidden} footer{visibility:hidden}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;margin-bottom:30px;padding-bottom:20px;border-bottom:2px solid rgba(128,128,128,0.2);">
  <h1 style="margin:0;font-size:2.5rem;color:#002060;">S.A.C.</h1>
  <div style="font-size:1.2rem;font-weight:600;opacity:0.8;">SISTEMA DE AVALIAÇÃO CURRICULAR</div>
  <div style="font-size:0.9rem;opacity:0.6;">PET ENGENHARIA QUÍMICA - UFC</div>
</div>
""", unsafe_allow_html=True)

def obter_hora_ceara():
    fuso = timezone(timedelta(hours=-3))
    return datetime.now(fuso).strftime("%Y-%m-%d %H:%M:%S")

# ==============================================================================
# ESTADOS DA APLICAÇÃO (AUTENTICAÇÃO E WIZARD)
# ==============================================================================
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "fase_transcricao" not in st.session_state: st.session_state.fase_transcricao = "configuracao"
if "aba_atual" not in st.session_state: st.session_state.aba_atual = SECOES[0]
if "respostas" not in st.session_state: st.session_state.respostas = {}

def obter_arquivo_rascunho():
    petiano = st.session_state.get("p_pet", "Padrao").replace(" ", "_")
    return f"rascunho_{petiano}.json"

def salvar_rascunho():
    if st.session_state.get("fase_transcricao") == "perguntas":
        try:
            with open(obter_arquivo_rascunho(), "w", encoding="utf-8") as f:
                json.dump(st.session_state.respostas, f)
        except Exception: pass

def carregar_rascunho():
    arquivo = obter_arquivo_rascunho()
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                st.session_state.respostas = json.load(f)
        except Exception: pass

def limpar_rascunho():
    st.session_state.respostas = {}
    arquivo = obter_arquivo_rascunho()
    if os.path.exists(arquivo):
        try: os.remove(arquivo)
        except Exception: pass

# ==============================================================================
# MENU LATERAL PRINCIPAL
# ==============================================================================
with st.sidebar:
    st.markdown("### 🌐 NAVEGAÇÃO")
    menu_principal = st.radio("Ir para:", ["📊 Dashboard Público", "🔒 Área Restrita"], label_visibility="collapsed")
    st.markdown("---")

# ==============================================================================
# PÁGINA 1: DASHBOARD PÚBLICO (ANÁLISE ROBUSTA)
# ==============================================================================
if menu_principal == "📊 Dashboard Público":
    
    # --- NOVO BLOCO: RESUMO DO PROJETO ---
    st.markdown("""
    <div style="background-color: #f0f4f8; padding: 20px; border-radius: 10px; border-left: 5px solid #002060; margin-bottom: 25px;">
        <h4 style="margin-top: 0; color: #002060;">📌 Sobre o Projeto S.A.C.</h4>
        <p style="margin-bottom: 10px; font-size: 1.05rem;">
            O <strong>Sistema de Avaliação Curricular</strong> é uma plataforma voltada para a avaliação das disciplinas e docentes do Departamento de Engenharia Química (DEQ) da UFC. Nosso objetivo é transformar a percepção dos discentes em dados estratégicos.
        </p>
        <p style="margin-bottom: 5px; font-weight: bold;">Com esses dados, buscamos:</p>
        <ul style="margin-top: 0; padding-left: 20px;">
            <li><strong>Apoiar a Coordenação:</strong> Analisar a eficácia e o impacto da nova matriz curricular (2023.1).</li>
            <li><strong>Garantir Qualidade:</strong> Verificar a aderência da formação acadêmica às competências exigidas pelo CREA.</li>
            <li><strong>Promover Evolução:</strong> Impulsionar um ciclo de melhoria contínua e fortalecer o diálogo entre alunos e professores.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    # -------------------------------------

    df = ler_banco_cacheados()
    
    if df.empty:
        st.info("📊 Nenhum dado encontrado para gerar análises no momento.")
    else:
        # 1. ÁREA DE FILTROS INTERATIVOS
        with st.expander("🔎 FILTROS DE ANÁLISE (Clique para expandir)", expanded=False):
            cf1, cf2 = st.columns(2)
            sems_disp = ["Todos"] + sorted([s for s in df['Semestre'].dropna().unique()])
            currs_disp = ["Todos"] + sorted([c for c in df['Curriculo'].dropna().unique()])
            
            f_sem = cf1.selectbox("Filtrar por Semestre:", sems_disp)
            f_curr = cf2.selectbox("Filtrar por Matriz Curricular:", currs_disp)
            
        df_filt = df.copy()
        if f_sem != "Todos": df_filt = df_filt[df_filt['Semestre'] == f_sem]
        if f_curr != "Todos": df_filt = df_filt[df_filt['Curriculo'] == f_curr]

        if df_filt.empty:
            st.warning("Nenhum discente corresponde aos filtros selecionados.")
        else:
            cols_notas = [id_ for id_, _ in ORDEM_QUESTOES if id_ in df_filt.columns]
            df_nums = df_filt[cols_notas].apply(pd.to_numeric, errors='coerce')
            media_geral = df_nums.mean().mean()
            
            # 2. INDICADORES CHAVE (KPIs)
            st.markdown("<br>", unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3)
            k1.markdown(f"""<div class='kpi-card'><div class='kpi-titulo'>Total de Avaliações</div><div class='kpi-valor'>{len(df_filt)}</div></div>""", unsafe_allow_html=True)
            k2.markdown(f"""<div class='kpi-card'><div class='kpi-titulo'>Média Global de Desempenho</div><div class='kpi-valor'>{media_geral:.2f} <span style='font-size:1rem;color:#999;'>/ 5.0</span></div></div>""", unsafe_allow_html=True)
            
            ultima_att = pd.to_datetime(df['Data_Registro']).max()
            data_str = ultima_att.strftime("%d/%m/%Y") if pd.notna(ultima_att) else "-"
            k3.markdown(f"""<div class='kpi-card'><div class='kpi-titulo'>Última Atualização</div><div class='kpi-valor' style='font-size:1.5rem; margin-top:10px;'>{data_str}</div></div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            medias_questoes = df_nums.mean().reset_index()
            medias_questoes.columns = ["ID", "Média"]
            medias_questoes["Competência"] = medias_questoes["ID"].map(ID_PARA_TEXTO)
            medias_questoes = medias_questoes.dropna().sort_values(by="Média", ascending=False)

            if len(medias_questoes) >= 2:
                top_1 = medias_questoes.iloc[0]['Competência']
                bot_1 = medias_questoes.iloc[-1]['Competência']
                st.info(f"💡 **Tradução Rápida dos Dados:** Atualmente, a maior fortaleza dos alunos analisados é **{top_1}**. Por outro lado, a área que exige maior atenção pedagógica e desenvolvimento é **{bot_1}**.")

            st.markdown("---")

            # 3. SISTEMA DE ABAS ORGANIZADAS
            tab_geral, tab_detalhada, tab_tabela = st.tabs(["🎯 Visão Global", "📊 Análise Profunda", "📑 Dados e Exportação"])

            # ABA 1: VISÃO GLOBAL
            with tab_geral:
                c_graf1, c_graf2 = st.columns(2)
                with c_graf1:
                    st.markdown("#### Desempenho por Macro Área")
                    st.caption("💡 **Como ler:** Este gráfico de radar (teia) mostra o equilíbrio das notas. Quanto mais a área colorida se expande para as bordas (em direção à nota 5.0), maior a proficiência geral dos alunos naquele bloco de disciplinas.")
                    
                    secoes_map = { "1. Gerais": cols_notas[:8], "2. Específicas": cols_notas[8:19], "3. Básicas": cols_notas[19:31], "4. Profissionais": cols_notas[31:41], "5. Avançadas": cols_notas[41:-1] }
                    medias_radar = []
                    for nome_secao, ids in secoes_map.items():
                        valid_ids = [i for i in ids if i in df_nums.columns]
                        if valid_ids:
                            media_secao = df_nums[valid_ids].mean().mean()
                            if pd.notna(media_secao): medias_radar.append({"Macro Área": nome_secao, "Média": media_secao})
                    
                    if medias_radar:
                        df_radar = pd.DataFrame(medias_radar)
                        fig_radar = px.line_polar(df_radar, r='Média', theta='Macro Área', line_close=True, range_r=[0, 5], markers=True)
                        fig_radar.update_traces(fill='toself', line_color='#002060')
                        st.plotly_chart(fig_radar, use_container_width=True)
                
                with c_graf2:
                    st.markdown("#### Evolução da Média por Semestre")
                    st.caption("💡 **Como ler:** Compara a média geral dos discentes agrupada pelo semestre cursado. Permite visualizar se os alunos adquirem mais segurança e competências técnicas à medida que chegam ao final do curso.")
                    
                    df_filt['Media_Aluno'] = df_nums.mean(axis=1)
                    media_por_semestre = df_filt.groupby('Semestre')['Media_Aluno'].mean().reset_index()
                    fig_bar_sem = px.bar(media_por_semestre, x='Semestre', y='Media_Aluno', text_auto='.2f', color='Media_Aluno', color_continuous_scale='Blues')
                    fig_bar_sem.update_layout(yaxis_range=[0, 5], coloraxis_showscale=False)
                    st.plotly_chart(fig_bar_sem, use_container_width=True)

            # ABA 2: ANÁLISE PROFUNDA
            with tab_detalhada:
                st.markdown("#### 🏆 Top 5 Fortalezas (Maiores Médias)")
                st.caption("💡 **Como ler:** Lista as 5 competências específicas onde os discentes relataram o **maior nível** de aprendizado e capacidade prática. Representa os pilares de sucesso do curso de acordo com a percepção dos alunos.")
                fig_top = px.bar(medias_questoes.head(5).sort_values('Média', ascending=True), 
                                 x='Média', y='Competência', orientation='h', text_auto='.2f')
                fig_top.update_traces(marker_color='#2ca02c') # Verde
                fig_top.update_layout(xaxis_range=[0, 5], height=300)
                st.plotly_chart(fig_top, use_container_width=True)

                st.markdown("#### 📉 Top 5 Oportunidades de Melhoria (Menores Médias)")
                st.caption("💡 **Como ler:** Lista as 5 competências com as **menores médias**. Estas são as áreas de alerta, indicando onde os alunos sentem mais dificuldade ou onde o currículo e metodologias de ensino podem ser fortalecidos.")
                fig_bot = px.bar(medias_questoes.tail(5), 
                                 x='Média', y='Competência', orientation='h', text_auto='.2f')
                fig_bot.update_traces(marker_color='#d62728') # Vermelho
                fig_bot.update_layout(xaxis_range=[0, 5], height=300)
                st.plotly_chart(fig_bot, use_container_width=True)

                if 'Curriculo' in df_filt.columns and df_filt['Curriculo'].nunique() > 1:
                    st.markdown("---")
                    st.markdown("#### 📦 Distribuição: Currículo Novo vs Antigo")
                    st.caption("💡 **Como ler:** Este Boxplot (diagrama de caixa) compara a variação das médias entre diferentes matrizes curriculares. A linha no meio da caixa é a mediana (o aluno do 'meio'). Caixas mais curtas indicam notas mais padronizadas, enquanto caixas longas apontam grande desigualdade de desempenho.")
                    fig_box = px.box(df_filt, x="Curriculo", y="Media_Aluno", color="Curriculo", points="all")
                    st.plotly_chart(fig_box, use_container_width=True)

            # ABA 3: TABELA DE DADOS
            with tab_tabela:
                st.markdown("#### Tabela Agregada de Competências")
                st.caption("Esta tabela apresenta a média técnica de cada competência baseada nos filtros aplicados. Dados pessoais dos alunos foram ocultados para garantir o anonimato ético da avaliação.")
                
                df_tabela = medias_questoes.copy()
                df_tabela["Média"] = df_tabela["Média"].round(2)
                df_tabela.rename(columns={"ID": "Código da Questão"}, inplace=True)
                
                st.dataframe(df_tabela, use_container_width=True, hide_index=True)
                
                csv = df_tabela.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 Baixar Dados em Excel/CSV",
                    data=csv,
                    file_name=f"sac_medias_competencias_{obter_hora_ceara()[:10]}.csv",
                    mime="text/csv",
                )

# ==============================================================================
# PÁGINA 2: ÁREA RESTRITA (REQUER SENHA)
# ==============================================================================
elif menu_principal == "🔒 Área Restrita":
    if not st.session_state.autenticado:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="login-box">
            <h3 style="color:#002060; margin-bottom: 5px;">Acesso Restrito</h3>
            <p style="font-size: 0.9rem; color: #666; margin-bottom: 20px;">Área exclusiva para Petianos</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            senha_digitada = st.text_input("Senha:", type="password", placeholder="Digite a senha...")
            if st.button("Autenticar 🔐", use_container_width=True, type="primary"):
                senha_correta = st.secrets.get("SENHA_PET", "petufc2026") 
                if senha_digitada == senha_correta:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta. Tente novamente.")
    else:
        with st.sidebar:
            st.markdown("### 🛠️ Módulos de Gestão")
            modo_operacao = st.radio("Ferramentas:", ["📝 Nova Transcrição", "✏️ Editar Registro"], label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Desconectar (Sair) 🚪", use_container_width=True):
                st.session_state.autenticado = False
                st.rerun()

        # ----------------------------------------------------------------------
        # MÓDULO A: NOVA TRANSCRIÇÃO
        # ----------------------------------------------------------------------
        if modo_operacao == "📝 Nova Transcrição":
            if st.session_state.fase_transcricao == "configuracao":
                st.markdown("### 👤 Etapa 1: Dados do Discente")
                st.info("Preencha as informações do formulário físico para liberar o ambiente de transcrição.")
                
                c1, c2 = st.columns(2)
                with c1:
                    nome_disc = st.text_input("Nome Completo do Discente", key="ident_nome", value=st.session_state.get("p_nome", ""))
                    mat_disc = st.text_input("Matrícula", key="ident_mat", value=st.session_state.get("p_mat", ""))
                    idx_sem = LISTA_SEMESTRES.index(st.session_state.get("p_sem", LISTA_SEMESTRES[0])) if st.session_state.get("p_sem") in LISTA_SEMESTRES else 0
                    sem_disc = st.selectbox("Semestre Vigente", LISTA_SEMESTRES, key="ident_sem", index=idx_sem)
                with c2:
                    idx_pet = LISTA_PETIANOS.index(st.session_state.get("p_pet", LISTA_PETIANOS[0])) if st.session_state.get("p_pet") in LISTA_PETIANOS else 0
                    petiano = st.selectbox("Petiano Responsável pela Transcrição", LISTA_PETIANOS, key="ident_pet", index=idx_pet)
                    idx_curr = LISTA_CURRICULOS.index(st.session_state.get("p_curr", LISTA_CURRICULOS[0])) if st.session_state.get("p_curr") in LISTA_CURRICULOS else 0
                    curr_disc = st.radio("Matriz Curricular", LISTA_CURRICULOS, key="ident_curr", index=idx_curr)
                    
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("INICIAR TRANSCRIÇÃO 🚀", type="primary", use_container_width=True):
                    if not st.session_state.get("ident_nome") or not st.session_state.get("ident_pet"):
                        st.error("⚠️ Atenção: É obrigatório informar o Nome do Discente e o Petiano Responsável.")
                    else:
                        st.session_state.p_nome = st.session_state.ident_nome
                        st.session_state.p_mat = st.session_state.ident_mat
                        st.session_state.p_sem = st.session_state.ident_sem
                        st.session_state.p_pet = st.session_state.ident_pet
                        st.session_state.p_curr = st.session_state.ident_curr
                        st.session_state.aba_atual = SECOES[0] 
                        carregar_rascunho()
                        with st.spinner(f"Preparando ambiente seguro para {st.session_state.p_nome}..."):
                            time.sleep(1.5) 
                        st.session_state.fase_transcricao = "perguntas"
                        st.rerun()

            elif st.session_state.fase_transcricao == "perguntas":
                st.markdown(f"""
                <div class="header-box">
                    <h4 style="margin-top:0; color:#002060;">📋 Ambiente de Transcrição Ativo</h4>
                    <strong>Discente:</strong> {st.session_state.get("p_nome", "")} ({st.session_state.get("p_mat", "")}) &nbsp;|&nbsp; 
                    <strong>Semestre:</strong> {st.session_state.get("p_sem", "")} &nbsp;|&nbsp; 
                    <strong>Responsável:</strong> {st.session_state.get("p_pet", "")}
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("⬅️ Voltar e Editar Dados do Discente"):
                    st.session_state.fase_transcricao = "configuracao"
                    st.rerun()
                    
                st.markdown("---")

                idx_aba_atual = SECOES.index(st.session_state.aba_atual)
                aba_ativa = st.radio("Navegação:", SECOES, index=idx_aba_atual, horizontal=True, label_visibility="collapsed")
                
                if aba_ativa != st.session_state.aba_atual:
                    st.session_state.aba_atual = aba_ativa
                    st.rerun()
                
                def cb_salvar_nota(id_):
                    st.session_state.respostas[f"nota_{id_}"] = st.session_state[f"wg_nota_{id_}"]
                    salvar_rascunho()

                def cb_salvar_obs(id_):
                    st.session_state.respostas[f"obs_{id_}"] = st.session_state[f"wg_obs_{id_}"]
                    salvar_rascunho()

                def renderizar_pergunta_nativa(id_, titulo):
                    with st.container():
                        st.markdown(f'<div class="pergunta-card"><div class="pergunta-texto">{ID_PARA_LABEL[id_]} — {titulo}</div></div>', unsafe_allow_html=True)
                        c1, c2 = st.columns([0.6, 0.4])
                        with c1:
                            val_nota = st.session_state.respostas.get(f"nota_{id_}", "N/A")
                            idx_nota = NOTA_LABELS.index(val_nota) if val_nota in NOTA_LABELS else 0
                            st.radio("Nota", NOTA_LABELS, index=idx_nota, horizontal=True, key=f"wg_nota_{id_}", on_change=cb_salvar_nota, args=(id_,), label_visibility="collapsed")
                        with c2:
                            val_obs = st.session_state.respostas.get(f"obs_{id_}", "")
                            st.text_input("Transcrição de Obs.", value=val_obs, placeholder="Comentários...", key=f"wg_obs_{id_}", on_change=cb_salvar_obs, args=(id_,), label_visibility="collapsed")

                blocos_questoes = {
                    SECOES[0]: ORDEM_QUESTOES[:8], SECOES[1]: ORDEM_QUESTOES[8:19], SECOES[2]: ORDEM_QUESTOES[19:31],
                    SECOES[3]: ORDEM_QUESTOES[31:41], SECOES[4]: ORDEM_QUESTOES[41:-1], SECOES[5]: [ORDEM_QUESTOES[-1]]
                }

                if st.session_state.aba_atual == SECOES[5]:
                    st.warning("⚠️ Obrigatório preencher a Reflexão Final. Se estiver vazio no papel, digite 'EM BRANCO'.")
                
                for id_, titulo in blocos_questoes[st.session_state.aba_atual]:
                    renderizar_pergunta_nativa(id_, titulo)

                st.markdown("---")

                if st.session_state.aba_atual != SECOES[5]:
                    col_vazia1, col_botao, col_vazia2 = st.columns([1, 2, 1])
                    with col_botao:
                        prox_secao = SECOES[idx_aba_atual + 1]
                        if st.button(f"AVANÇAR PARA: {prox_secao} ➡️", use_container_width=True):
                            st.session_state.aba_atual = prox_secao
                            st.rerun()
                else:
                    st.markdown("#### TRANSCRIÇÃO DAS RESPOSTAS ABERTAS")
                    def cb_salvar_aberta(chave):
                        st.session_state.respostas[chave] = st.session_state[f"wg_{chave}"]
                        salvar_rascunho()

                    txt_fortes = st.text_area("Pontos Fortes *", value=st.session_state.respostas.get("obs_fortes", ""), key="wg_obs_fortes", on_change=cb_salvar_aberta, args=("obs_fortes",))
                    txt_fracos = st.text_area("Pontos a Desenvolver *", value=st.session_state.respostas.get("obs_fracos", ""), key="wg_obs_fracos", on_change=cb_salvar_aberta, args=("obs_fracos",))
                    txt_prat   = st.text_area("Contribuição Prática", value=st.session_state.respostas.get("obs_prat", ""), key="wg_obs_prat", on_change=cb_salvar_aberta, args=("obs_prat",))
                    txt_ex     = st.text_area("Exemplos de Aplicação", value=st.session_state.respostas.get("obs_ex", ""), key="wg_obs_ex", on_change=cb_salvar_aberta, args=("obs_ex",))
                    txt_fut1   = st.text_area("Competências Futuras", value=st.session_state.respostas.get("obs_fut1", ""), key="wg_obs_fut1", on_change=cb_salvar_aberta, args=("obs_fut1",))
                    txt_fut2   = st.text_area("Plano de Desenvolvimento", value=st.session_state.respostas.get("obs_fut2", ""), key="wg_obs_fut2", on_change=cb_salvar_aberta, args=("obs_fut2",))
                    txt_final  = st.text_area("Comentários Finais *", value=st.session_state.respostas.get("obs_final", ""), key="wg_obs_final", on_change=cb_salvar_aberta, args=("obs_final",))

                    st.markdown("---")
                    if st.button("💾 FINALIZAR E SALVAR REGISTRO", type="primary", use_container_width=True):
                        erros = []
                        if not st.session_state.respostas.get("obs_fortes", "").strip(): erros.append("Pontos Fortes")
                        if not st.session_state.respostas.get("obs_fracos", "").strip(): erros.append("Pontos a Desenvolver")
                        if not st.session_state.respostas.get("obs_final", "").strip(): erros.append("Comentários Finais")

                        if erros:
                            st.error(f"❌ IMPOSSÍVEL SALVAR. Faltam campos obrigatórios: {', '.join(erros)}")
                        else:
                            dados_salvar = {
                                "Registro_ID": str(uuid.uuid4()),
                                "Petiano_Responsavel": st.session_state.p_pet, "Nome": st.session_state.p_nome,
                                "Matricula": st.session_state.p_mat, "Semestre": st.session_state.p_sem,
                                "Curriculo": st.session_state.p_curr, "Data_Registro": obter_hora_ceara(),
                                "Autoavaliação: Pontos Fortes": st.session_state.respostas.get("obs_fortes", "").strip(),
                                "Autoavaliação: Pontos a Desenvolver": st.session_state.respostas.get("obs_fracos", "").strip(),
                                "Contribuição Prática": st.session_state.respostas.get("obs_prat", "").strip(),
                                "Exemplos de Aplicação": st.session_state.respostas.get("obs_ex", "").strip(),
                                "Competências Futuras": st.session_state.respostas.get("obs_fut1", "").strip(),
                                "Plano de Desenvolvimento": st.session_state.respostas.get("obs_fut2", "").strip(),
                                "Observações Finais": st.session_state.respostas.get("obs_final", "").strip(),
                            }
                            for id_, _ in ORDEM_QUESTOES:
                                dados_salvar[id_] = st.session_state.respostas.get(f"nota_{id_}", "N/A")
                                dados_salvar[f"Obs_{id_}"] = st.session_state.respostas.get(f"obs_{id_}", "")
                            
                            try:
                                inserir_registro(dados_salvar)
                                limpar_rascunho()
                                st.balloons(); st.success("✅ Transcrição salva com sucesso no banco de dados!")
                                st.session_state.clear(); st.session_state.autenticado = True
                                st.session_state.fase_transcricao = "configuracao"; st.session_state.aba_atual = SECOES[0]
                                time.sleep(2); st.rerun()
                            except Exception as e:
                                st.error(f"❌ ERRO ao salvar no banco: {e}")

        # ----------------------------------------------------------------------
        # MÓDULO B: EDIÇÃO DE REGISTRO
        # ----------------------------------------------------------------------
        elif modo_operacao == "✏️ Editar Registro":
            st.markdown("### ✏️ EDIÇÃO EM LOTE")
            st.markdown("<div class='edit-warning'>Edite diretamente na tabela para corrigir múltiplas notas de uma só vez.</div>", unsafe_allow_html=True)

            df = ler_banco_cacheados()
            if df.empty:
                st.warning("Banco de dados vazio.")
            else:
                aluno_busca = st.selectbox("Selecione o registro para corrigir:", df.apply(lambda x: f"{x['Registro_ID']} • {x['Nome']} ({x['Matricula']})", axis=1).tolist())
                sel_id = aluno_busca.split(" • ")[0].strip()
                aluno_dados = df[df['Registro_ID'] == sel_id].iloc[0]

                st.subheader("1. Edição de Notas (Planilha Dinâmica)")
                cols_notas = [id_ for id_, _ in ORDEM_QUESTOES if id_ in df.columns]
                df_notas = pd.DataFrame({
                    "Questão": [ID_PARA_LABEL[id_] for id_ in cols_notas],
                    "Descrição": [ID_PARA_TEXTO[id_] for id_ in cols_notas],
                    "Nota_Atual": [aluno_dados.get(id_, "N/A") for id_ in cols_notas]
                })
                
                df_notas_editado = st.data_editor(
                    df_notas, column_config={"Nota_Atual": st.column_config.SelectboxColumn("Sua Nova Nota", options=NOTA_LABELS, required=True)},
                    disabled=["Questão", "Descrição"], hide_index=True, use_container_width=True
                )

                st.markdown("---")
                if st.button("💾 SALVAR TODAS AS ALTERAÇÕES", type="primary", icon=":material/update:"):
                    novos_dados = {}
                    for i, row in df_notas_editado.iterrows():
                        id_real = cols_notas[i]
                        novos_dados[id_real] = row["Nota_Atual"]
                    
                    try:
                        atualizar_registro(sel_id, novos_dados)
                        st.success("Notas atualizadas em lote com sucesso!")
                        time.sleep(1.5); st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")
