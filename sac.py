# app.py
import uuid
from datetime import datetime, timedelta, timezone
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Importações dos novos módulos
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
div[role="radiogroup"] { flex-direction: row; gap: 15px; } /* Força os radios a ficarem horizontais */
.edit-warning { padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; background-color: #fff3e0; color: #e65100; }
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
# BARRA LATERAL
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ MODO DE OPERAÇÃO")
    modo_operacao = st.radio("Selecione:", ["📝 Nova Transcrição", "✏️ Editar Registro", "📊 Painel Gerencial"], label_visibility="collapsed")
    
    if modo_operacao == "📝 Nova Transcrição":
        st.markdown("---")
        st.markdown("#### 👤 Identificação")
        petiano = st.selectbox("Responsável", LISTA_PETIANOS, key="ident_pet")
        nome_disc = st.text_input("Nome do Discente", key="ident_nome")
        mat_disc = st.text_input("Matrícula", key="ident_mat")
        sem_disc = st.selectbox("Semestre", LISTA_SEMESTRES, key="ident_sem")
        curr_disc = st.radio("Matriz", LISTA_CURRICULOS, key="ident_curr")
        
        if st.button("Limpar Formulário Inteiro", icon=":material/delete:"):
            st.session_state.clear()
            st.rerun()

# ==============================================================================
# 1) NOVA TRANSCRIÇÃO (UX Otimizada com st.tabs e st.radio horizontal)
# ==============================================================================
if modo_operacao == "📝 Nova Transcrição":
    # Substituímos a navegação customizada e complexa pelas abas nativas do Streamlit!
    abas = st.tabs(SECOES)
    
    def renderizar_pergunta_nativa(id_, titulo):
        with st.container():
            st.markdown(f'<div class="pergunta-card"><div class="pergunta-texto">{ID_PARA_LABEL[id_]} — {titulo}</div></div>', unsafe_allow_html=True)
            c1, c2 = st.columns([0.6, 0.4])
            with c1:
                # Adeus código complexo de checkbox! Olá radio horizontal nativo!
                st.radio("Nota", NOTA_LABELS, horizontal=True, key=f"nota_{id_}", label_visibility="collapsed")
            with c2:
                st.text_input("Transcrição de Obs.", placeholder="Comentários...", key=f"obs_{id_}", label_visibility="collapsed")

    # Mapeamento do conteúdo para cada aba
    com_blocos = [
        (abas[0], ORDEM_QUESTOES[:8]),
        (abas[1], ORDEM_QUESTOES[8:19]),
        (abas[2], ORDEM_QUESTOES[19:31]),
        (abas[3], ORDEM_QUESTOES[31:41]),
        (abas[4], ORDEM_QUESTOES[41:-1])
    ]

    for aba, questoes in com_blocos:
        with aba:
            for id_, titulo in questoes:
                renderizar_pergunta_nativa(id_, titulo)

    # Aba de Reflexão Final e Salvamento
    with abas[5]:
        st.warning("⚠️ Obrigatório preencher a Reflexão Final. Se estiver vazio no papel, digite 'EM BRANCO'.")
        renderizar_pergunta_nativa(ORDEM_QUESTOES[-1][0], ORDEM_QUESTOES[-1][1])
        
        st.markdown("#### TRANSCRIÇÃO DAS RESPOSTAS ABERTAS")
        txt_fortes = st.text_area("Pontos Fortes *", key="obs_fortes")
        txt_fracos = st.text_area("Pontos a Desenvolver *", key="obs_fracos")
        txt_prat   = st.text_area("Contribuição Prática", key="obs_prat")
        txt_ex     = st.text_area("Exemplos de Aplicação", key="obs_ex")
        txt_fut1   = st.text_area("Competências Futuras", key="obs_fut1")
        txt_fut2   = st.text_area("Plano de Desenvolvimento", key="obs_fut2")
        txt_final  = st.text_area("Comentários Finais *", key="obs_final")

        st.markdown("---")
        if st.button("FINALIZAR E SALVAR REGISTRO", type="primary", use_container_width=True):
            erros = []
            if not st.session_state.get("ident_nome"): erros.append("Nome do Discente")
            if not st.session_state.get("ident_pet"): erros.append("Petiano Responsável")
            if not txt_fortes: erros.append("Pontos Fortes")
            if not txt_fracos: erros.append("Pontos a Desenvolver")
            if not txt_final: erros.append("Comentários Finais")

            if erros:
                st.error(f"❌ IMPOSSÍVEL SALVAR. Faltam os campos obrigatórios: {', '.join(erros)}")
            else:
                dados_salvar = {
                    "Registro_ID": str(uuid.uuid4()),
                    "Petiano_Responsavel": st.session_state["ident_pet"],
                    "Nome": st.session_state["ident_nome"],
                    "Matricula": st.session_state["ident_mat"],
                    "Semestre": st.session_state["ident_sem"],
                    "Curriculo": st.session_state["ident_curr"],
                    "Data_Registro": obter_hora_ceara(),
                    "Autoavaliação: Pontos Fortes": txt_fortes.strip(),
                    "Autoavaliação: Pontos a Desenvolver": txt_fracos.strip(),
                    "Contribuição Prática": txt_prat.strip(),
                    "Exemplos de Aplicação": txt_ex.strip(),
                    "Competências Futuras": txt_fut1.strip(),
                    "Plano de Desenvolvimento": txt_fut2.strip(),
                    "Observações Finais": txt_final.strip(),
                }
                # Coleta as notas dinamicamente
                for id_, _ in ORDEM_QUESTOES:
                    dados_salvar[id_] = st.session_state.get(f"nota_{id_}", "N/A")
                    dados_salvar[f"Obs_{id_}"] = st.session_state.get(f"obs_{id_}", "")
                
                try:
                    inserir_registro(dados_salvar)
                    st.balloons()
                    st.success("✅ Transcrição salva com sucesso no banco de dados!")
                    st.session_state.clear() # Limpa o formulário após salvar
                except Exception as e:
                    st.error(f"❌ ERRO ao salvar no banco: {e}")

# ==============================================================================
# 2) EDIÇÃO DE REGISTRO (Bulk Edit com st.data_editor)
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
        # Transforma os dados numa tabela editável vertical para melhor UX
        cols_notas = [id_ for id_, _ in ORDEM_QUESTOES if id_ in df.columns]
        df_notas = pd.DataFrame({
            "Questão": [ID_PARA_LABEL[id_] for id_ in cols_notas],
            "Descrição": [ID_PARA_TEXTO[id_] for id_ in cols_notas],
            "Nota_Atual": [aluno_dados.get(id_, "N/A") for id_ in cols_notas]
        })
        
        # st.data_editor permite edição direto na tabela parecendo Excel!
        df_notas_editado = st.data_editor(
            df_notas, 
            column_config={"Nota_Atual": st.column_config.SelectboxColumn("Sua Nova Nota", options=NOTA_LABELS, required=True)},
            disabled=["Questão", "Descrição"],
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")
        if st.button("💾 SALVAR TODAS AS ALTERAÇÕES", type="primary", icon=":material/update:"):
            # Constrói o dicionário de update
            novos_dados = {}
            for i, row in df_notas_editado.iterrows():
                id_real = cols_notas[i]
                novos_dados[id_real] = row["Nota_Atual"]
            
            try:
                atualizar_registro(sel_id, novos_dados)
                st.success("Notas atualizadas em lote com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")

# ==============================================================================
# 3) PAINEL GERENCIAL (Com Radar Chart e Comparação Curricular)
# ==============================================================================
elif modo_operacao == "📊 Painel Gerencial":
    st.markdown("### 📊 DASHBOARD DE INTELIGÊNCIA CURRICULAR")
    df = ler_banco_cacheados()
    
    if df.empty:
        st.info("Nenhum dado encontrado para gerar gráficos.")
    else:
        # KPI's Iniciais
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Avaliações", len(df))
        
        # Filtros de Dados Puros
        cols_notas = [id_ for id_, _ in ORDEM_QUESTOES if id_ in df.columns]
        df_nums = df[cols_notas].apply(pd.to_numeric, errors='coerce')
        media_geral = df_nums.mean().mean()
        c2.metric("Média Global do Curso", f"{media_geral:.2f}/5.0")
        c3.metric("Última Atualização", pd.to_datetime(df['Data_Registro']).max().strftime("%d/%m/%y %H:%M"))

        st.markdown("---")
        
        # Gráfico 1: Comparação de Matrizes Curriculares
        st.subheader("📈 Desempenho: Currículo Novo vs Antigo")
        if 'Curriculo' in df.columns and df['Curriculo'].nunique() > 1:
            df['Media_Aluno'] = df_nums.mean(axis=1)
            fig_box = px.box(df, x="Curriculo", y="Media_Aluno", color="Curriculo", 
                             title="Distribuição das Médias Gerais por Matriz Curricular")
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.caption("Apenas uma matriz curricular cadastrada no momento para comparação.")

        # Gráfico 2: Radar Chart (Competências por Seção)
        st.markdown("---")
        st.subheader("🎯 Mapeamento de Competências (Gráfico de Radar)")
        
        # Calculando a média agregada por Seção (1 a 5)
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
                medias_radar.append({"Macro Área": nome_secao, "Média": media_secao})
        
        df_radar = pd.DataFrame(medias_radar)
        
        if not df_radar.empty:
            fig_radar = px.line_polar(df_radar, r='Média', theta='Macro Área', line_close=True,
                                      range_r=[0, 5], markers=True, title="Desempenho Médio Global por Macro Área")
            fig_radar.update_traces(fill='toself', line_color='#002060')
            st.plotly_chart(fig_radar, use_container_width=True)
