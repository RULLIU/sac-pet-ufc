# app.py / sac.py
import os
import json
import uuid
import time
from datetime import datetime, timedelta, timezone
import streamlit as st
import pandas as pd
import plotly.express as px

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
.pergunta-card {
    background-color: #ffffff; border-radius: 8px; padding: 16px 24px; margin-bottom: 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04); border-left: 6px solid #002060; border: 1px solid #edf2f7;
}
.pergunta-texto { font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; color: #1e1e1e; }
div[role="radiogroup"] { flex-direction: row; gap: 15px; } 
.edit-warning { padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; background-color: #fff3e0; color: #e65100; }
.header-box { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
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
# MOTOR DE AUTOSAVE E ESTADO
# ==============================================================================
if "fase_transcricao" not in st.session_state: st.session_state.fase_transcricao = "configuracao"
if "aba_atual" not in st.session_state: st.session_state.aba_atual = SECOES[0]
if "respostas" not in st.session_state: st.session_state.respostas = {}

def obter_arquivo_rascunho():
    """Gera um nome de arquivo isolado para cada Petiano"""
    petiano = st.session_state.get("p_pet", "Padrao").replace(" ", "_")
    return f"rascunho_{petiano}.json"

def salvar_rascunho():
    """Salva as respostas atuais no disco físico (Disparado a cada clique)"""
    if st.session_state.get("fase_transcricao") == "perguntas":
        try:
            with open(obter_arquivo_rascunho(), "w", encoding="utf-8") as f:
                json.dump(st.session_state.respostas, f)
        except Exception:
            pass

def carregar_rascunho():
    """Tenta puxar o rascunho anterior ao iniciar a transcrição"""
    arquivo = obter_arquivo_rascunho()
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                st.session_state.respostas = json.load(f)
        except Exception:
            pass

def limpar_rascunho():
    """Apaga o rascunho após salvar no banco de dados"""
    st.session_state.respostas = {}
    arquivo = obter_arquivo_rascunho()
    if os.path.exists(arquivo):
        try: os.remove(arquivo)
        except Exception: pass

# ==============================================================================
# BARRA LATERAL 
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ MÓDULOS")
    modo_operacao = st.radio("Selecione:", ["📝 Nova Transcrição", "✏️ Editar Registro", "📊 Painel Gerencial"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("A navegação global é feita por aqui.")

# ==============================================================================
# 1) NOVA TRANSCRIÇÃO 
# ==============================================================================
if modo_operacao == "📝 Nova Transcrição":
    
    # ETAPA 1: PÁGINA PRINCIPAL DE IDENTIFICAÇÃO
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
                
                # Carrega o rascunho anterior desse petiano (se existir)
                carregar_rascunho()
                
                with st.spinner(f"Preparando ambiente seguro para o discente {st.session_state.p_nome}..."):
                    time.sleep(1.5) 
                st.session_state.fase_transcricao = "perguntas"
                st.rerun()

    # ETAPA 2: MÓDULO DE TRANSCRIÇÃO DAS PERGUNTAS
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
        
        # Callbacks que disparam o autosave sempre que houver clique/digitação
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
            SECOES[0]: ORDEM_QUESTOES[:8],
            SECOES[1]: ORDEM_QUESTOES[8:19],
            SECOES[2]: ORDEM_QUESTOES[19:31],
            SECOES[3]: ORDEM_QUESTOES[31:41],
            SECOES[4]: ORDEM_QUESTOES[41:-1],
            SECOES[5]: [ORDEM_QUESTOES[-1]]
        }

        if st.session_state.aba_atual == SECOES[5]:
            st.warning("⚠️ Obrigatório preencher a Reflexão Final. Se estiver vazio no papel, digite 'EM BRANCO'.")
        
        for id_, titulo in blocos_questoes[st.session_state.aba_atual]:
            renderizar_pergunta_nativa(id_, titulo)

        st.markdown("---")

        # NAVEGAÇÃO E SALVAMENTO
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
                        "Petiano_Responsavel": st.session_state.p_pet,
                        "Nome": st.session_state.p_nome,
                        "Matricula": st.session_state.p_mat,
                        "Semestre": st.session_state.p_sem,
                        "Curriculo": st.session_state.p_curr,
                        "Data_Registro": obter_hora_ceara(),
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
                        limpar_rascunho() # Magia acontece aqui: apaga o json temporário
                        
                        st.balloons()
                        st.success("✅ Transcrição salva com sucesso no banco de dados!")
                        
                        # Reseta os dados temporários
                        st.session_state.clear() 
                        st.session_state.fase_transcricao = "configuracao"
                        st.session_state.aba_atual = SECOES[0]
                        time.sleep(2) 
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ ERRO ao salvar no banco: {e}")

# ==============================================================================
# 2) EDIÇÃO DE REGISTRO
# ==============================================================================
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
            df_notas, 
            column_config={"Nota_Atual": st.column_config.SelectboxColumn("Sua Nova Nota", options=NOTA_LABELS, required=True)},
            disabled=["Questão", "Descrição"],
            hide_index=True,
            use_container_width=True
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
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")

# ==============================================================================
# 3) PAINEL GERENCIAL
# ==============================================================================
elif modo_operacao == "📊 Painel Gerencial":
    st.markdown("### 📊 DASHBOARD DE INTELIGÊNCIA CURRICULAR")
    df = ler_banco_cacheados()
    
    if df.empty:
        st.info("Nenhum dado encontrado para gerar gráficos.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Avaliações", len(df))
        
        cols_notas = [id_ for id_, _ in ORDEM_QUESTOES if id_ in df.columns]
        df_nums = df[cols_notas].apply(pd.to_numeric, errors='coerce')
        media_geral = df_nums.mean().mean()
        c2.metric("Média Global do Curso", f"{media_geral:.2f}/5.0")
        
        ultima_att = pd.to_datetime(df['Data_Registro']).max()
        c3.metric("Última Atualização", ultima_att.strftime("%d/%m/%y %H:%M") if pd.notna(ultima_att) else "-")

        st.markdown("---")
        
        st.subheader("📈 Desempenho: Currículo Novo vs Antigo")
        if 'Curriculo' in df.columns and df['Curriculo'].nunique() > 1:
            df['Media_Aluno'] = df_nums.mean(axis=1)
            fig_box = px.box(df, x="Curriculo", y="Media_Aluno", color="Curriculo", 
                             title="Distribuição das Médias Gerais por Matriz Curricular")
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.caption("Apenas uma matriz curricular cadastrada no momento para comparação.")

        st.markdown("---")
        st.subheader("🎯 Mapeamento de Competências (Gráfico de Radar)")
        
        secoes_map = {
            "1. Gerais": cols_notas[:8],
            "2. Específicas": cols_notas[8:19],
            "3. Básicas": cols_notas[19:31],
            "4. Profissionais": cols_notas[31:41],
            "5. Avançadas": cols_notas[41:-1]
        }
        
        medias_radar = []
        for nome_secao, ids in secoes_map.items():
            valid_ids = [i for i in ids if i in df_nums.columns]
            if valid_ids:
                media_secao = df_nums[valid_ids].mean().mean()
                if pd.notna(media_secao):
                    medias_radar.append({"Macro Área": nome_secao, "Média": media_secao})
        
        df_radar = pd.DataFrame(medias_radar)
        
        if not df_radar.empty:
            fig_radar = px.line_polar(df_radar, r='Média', theta='Macro Área', line_close=True,
                                      range_r=[0, 5], markers=True, title="Desempenho Médio Global por Macro Área")
            fig_radar.update_traces(fill='toself', line_color='#002060')
            st.plotly_chart(fig_radar, use_container_width=True)
