# app.py
import os
import json
import uuid
from datetime import datetime, timedelta, timezone

import streamlit as st
import pandas as pd
import plotly.express as px
from st_supabase_connection import SupabaseConnection

# ==============================================================================
# 1) CONFIGURAÇÕES E CONEXÃO
# ==============================================================================
st.set_page_config(
    page_title="S.A.C. - PET Engenharia Química",
    layout="wide",
    page_icon="📝",
    initial_sidebar_state="expanded",
)

# Inicializa a conexão com o Supabase
conn = st.connection("supabase", type=SupabaseConnection)

ARQUIVO_BACKUP = "_backup_autosave.json"

# ==============================================================================
# 2) ESTILO PREMIUM (CSS CORRIGIDO)
# ==============================================================================
st.markdown("""
<style>
:root { --primary-color: #002060; }
.stApp { font-family: 'Segoe UI', 'Roboto', sans-serif; }

h1, h2, h3, h4 {
    color: var(--primary-color) !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Cartão da Pergunta - Visual Limpo e Fixo */
.pergunta-card {
    background-color: #ffffff !important;
    border-radius: 8px;
    padding: 16px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    border-left: 6px solid #002060 !important;
    border-top: 1px solid #edf2f7 !important;
    border-right: 1px solid #edf2f7 !important;
    border-bottom: 1px solid #edf2f7 !important;
}

/* Texto da Pergunta */
.pergunta-texto {
    font-size: 1.1rem;
    font-weight: 700;
    margin: 0;
    color: #1e1e1e !important; /* Força o texto a aparecer escuro e legível */
    opacity: 0.95;
}

/* Botões */
.stButton button { border-radius: 6px; font-weight: 700; text-transform: uppercase; height: 3.5em; width: 100%; transition: all 0.3s ease; }
.botao-avancar button { background-color: transparent; border: 2px solid #002060; color: #002060; }
.botao-avancar button:hover { background-color: #002060; color: white; transform: translateX(5px); }
.botao-final button { background-color: #002060 !important; color: white !important; border: none; height: 4.5em; font-size: 1.1rem; }
.botao-final button:hover { background-color: #003399 !important; transform: scale(1.02); }

/* Avisos do Modo de Edição */
.edit-warning { 
    padding: 15px; 
    border-radius: 8px; 
    margin-bottom: 20px; 
    text-align: center; 
    font-weight: bold; 
    background-color: #fff3e0 !important; 
    color: #e65100 !important; 
    border: 1px solid #ffe0b2 !important; 
}

/* Ocultar menus padrão do Streamlit */
#MainMenu{visibility:hidden} footer{visibility:hidden}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3) CABEÇALHO
# ==============================================================================
st.markdown("""
<div style="text-align:center;margin-bottom:30px;padding-bottom:20px;border-bottom:2px solid rgba(128,128,128,0.2);">
  <h1 style="margin:0;font-size:2.5rem;">S.A.C.</h1>
  <div style="font-size:1.2rem;font-weight:600;opacity:0.8;">SISTEMA DE AVALIAÇÃO CURRICULAR - MÓDULO DE TRANSCRIÇÃO</div>
  <div style="font-size:0.9rem;opacity:0.6;margin-top:5px;">PET ENGENHARIA QUÍMICA - UNIVERSIDADE FEDERAL DO CEARÁ</div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4) SUPORTE E BANCO DE DADOS
# ==============================================================================
SECOES = ["1. Gerais", "2. Específicas", "3. Básicas", "4. Profissionais", "5. Avançadas", "6. Reflexão"]
LISTA_PETIANOS = sorted(["", "Ana Carolina", "Ana Clara", "Ana Júlia", "Eric Rullian", "Gildelandio Junior", "Lucas Mossmann (trainee)", "Pedro Paulo"])
LISTA_SEMESTRES = [f"{i}º Semestre" for i in range(1, 11)]
LISTA_CURRICULOS = ["Novo (2023.1)", "Antigo (2005.1)", "Troca de Matriz (Velha -> Nova)"]

def ler_banco():
    try:
        response = conn.query("*", table="respostas_sac", ttl=0).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao ligar ao banco de dados: {e}")
        return pd.DataFrame()

if "nav_etapa" not in st.session_state:
    st.session_state["nav_etapa"] = SECOES[0]
if 'form_key' not in st.session_state:
    st.session_state.form_key = 0

def carregar_backup():
    if os.path.exists(ARQUIVO_BACKUP):
        try:
            with open(ARQUIVO_BACKUP, "r", encoding='utf-8') as f:
                dados = json.load(f)
                for k, v in dados.items():
                    if k.endswith(f"_{st.session_state.form_key}"):
                        st.session_state[k] = v
        except Exception:
            pass

if 'backup_restaurado' not in st.session_state:
    carregar_backup()
    st.session_state.backup_restaurado = True

def salvar_estado():
    try:
        dados_salvar = {k: v for k, v in st.session_state.items() if (k.startswith(("nota_", "obs_", "ident_"))) and isinstance(v, (str, int, float, bool))}
        with open(ARQUIVO_BACKUP, "w", encoding='utf-8') as f:
            json.dump(dados_salvar, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def navegar_proxima():
    try:
        idx = SECOES.index(st.session_state["nav_etapa"])
        if idx < len(SECOES) - 1:
            st.session_state["nav_etapa"] = SECOES[idx + 1]
            salvar_estado()
            st.rerun()
    except Exception:
        pass

def limpar_formulario():
    st.session_state.form_key += 1
    st.session_state["nav_etapa"] = SECOES[0]
    if os.path.exists(ARQUIVO_BACKUP):
        try: os.remove(ARQUIVO_BACKUP)
        except Exception: pass

def obter_hora_ceara():
    fuso = timezone(timedelta(hours=-3))
    return datetime.now(fuso).strftime("%Y-%m-%d %H:%M:%S")

# ==============================================================================
# 5) CHECKBOXES EXCLUSIVOS E RENDERIZAÇÃO
# ==============================================================================
NOTA_LABELS = ["N/A", "0", "1", "2", "3", "4", "5"]

def _on_checkbox_change(grupo_id: str, label_clicked: str, labels: list, k_suffix: str):
    nota_key = f"nota_{grupo_id}{k_suffix}"
    cb_key = f"cb_{grupo_id}_{label_clicked}{k_suffix}"
    current = st.session_state.get(cb_key, False)
    if current:
        st.session_state[nota_key] = label_clicked
        for lab in labels:
            st.session_state[f"cb_{grupo_id}_{lab}{k_suffix}"] = (lab == label_clicked)
    else:
        sel = st.session_state.get(nota_key, "N/A")
        for lab in labels:
            st.session_state[f"cb_{grupo_id}_{lab}{k_suffix}"] = (lab == sel)

def renderizar_pergunta(texto_pergunta, id_unica, valor_padrao="N/A", obs_padrao="", key_suffix=""):
    k = key_suffix if key_suffix else f"_{st.session_state.form_key}"
    labels = NOTA_LABELS

    nota_key = f"nota_{id_unica}{k}"
    if nota_key not in st.session_state or st.session_state[nota_key] not in labels:
        st.session_state[nota_key] = str(valor_padrao) if str(valor_padrao) in labels else "N/A"
    selected = st.session_state[nota_key]
    for lab in labels:
        cb_key = f"cb_{id_unica}_{lab}{k}"
        if cb_key not in st.session_state:
            st.session_state[cb_key] = (lab == selected)

    with st.container():
        st.markdown(f"""<div class="pergunta-card"><div class="pergunta-texto">{texto_pergunta}</div></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            cols = st.columns(len(labels))
            for i, lab in enumerate(labels):
                cb_key = f"cb_{id_unica}_{lab}{k}"
                cols[i].checkbox(
                    lab,
                    value=st.session_state.get(cb_key, lab == selected),
                    key=cb_key,
                    on_change=_on_checkbox_change,
                    args=(id_unica, lab, labels, k),
                    help="Selecione apenas uma opção."
                )
        with c2:
            st.text_input(
                "Transcrição de Obs.",
                value=str(obs_padrao) if pd.notna(obs_padrao) else "",
                placeholder="Comentários...",
                key=f"obs_{id_unica}{k}"
            )

# ==============================================================================
# 6) MAPA DE QUESTÕES
# ==============================================================================
ORDEM_QUESTOES = [
    ("q1",  "Projetar e conduzir experimentos e interpretar resultados"),
    ("q2",  "Desenvolver e/ou utilizar novas ferramentas e técnicas"),
    ("q3",  "Conceber, projetar e analisar sistemas, produtos e processos"),
    ("q4",  "Formular, conceber e avaliar soluções para problemas de engenharia"),
    ("q5",  "Analisar e compreender fenômenos físicos e químicos através de modelos"),
    ("q6",  "Comunicação técnica"),
    ("q7",  "Trabalhar e liderar equipes profissionais"),
    ("q8",  "Aplicar ética e legislação no exercício profissional"),
    ("q9",  "Aplicar conhecimentos matemáticos, científicos e tecnológicos"),
    ("q10", "Compreender e modelar transferência de quantidade de movimento, calor e massa"),
    ("q11", "Aplicar conhecimentos de fenômenos de transporte ao projeto"),
    ("q12", "Compreender mecanismos de transformação da matéria e energia"),
    ("q13", "Projetar sistemas de recuperação, separação e purificação"),
    ("q14", "Compreender mecanismos cinéticos de reações químicas"),
    ("q15", "Projetar e otimizar sistemas reacionais e reatores"),
    ("q16", "Projetar sistemas de controle de processos industriais"),
    ("q17", "Projetar e otimizar plantas industriais considerando ambiente e segurança"),
    ("q18", "Aplicação de conhecimentos em projeto básico e dimensionamento"),
    ("q19", "Execução de projetos de produção e melhorias de processos"),
    ("calc_21",   "Cálculo: Analisar grandes volumes de dados"),
    ("calc_52",   "Cálculo: Formação Básica"),
    ("fis_22",    "Física: Analisar criticamente a operação e manutenção de sistemas"),
    ("fis_53",    "Física: Ciência da Engenharia"),
    ("qui_23",    "Química: Aplicar conhecimentos de transformação a processos"),
    ("qui_24",    "Química: Conceber e desenvolver produtos e processos"),
    ("termo_25",  "Termodinâmica: Projetar sistemas de suprimento energético"),
    ("termo_54",  "Termodinâmica: Ciência da Engenharia Química"),
    ("ft_26",     "Fenômenos de Transporte: Aplicar conhecimentos de fenômenos de transporte"),
    ("ft_27",     "Fenômenos de Transporte: Comunicação técnica e recursos gráficos"),
    ("mecflu_28", "Mecânica dos Fluidos: Implantar, implementar e controlar soluções"),
    ("mecflu_29", "Mecânica dos Fluidos: Operar e supervisionar instalações"),
    ("op1_30",  "Operações Unitárias I: Inspecionar manutenção"),
    ("op1_55",  "Operações Unitárias I: Tecnologia Industrial"),
    ("op2_31",  "Operações Unitárias II: Elaborar estudos ambientais"),
    ("op2_32",  "Operações Unitárias II: Projetar tratamento ambiental"),
    ("reat_33", "Reatores Químicos: Gerir recursos"),
    ("reat_34", "Reatores Químicos: Controle de qualidade"),
    ("ctrl_35", "Controle de Processos: Supervisão"),
    ("ctrl_36", "Projetos: Gestão de empreendimentos"),
    ("proj_56", "Projetos: Gestão Industrial"),
    ("proj_57", "Projetos: Ética e Humanidades"),
    ("econ_37",  "Engenharia Econômica: Novos conceitos"),
    ("econ_38",  "Engenharia Econômica: Visão global"),
    ("gest_39",  "Gestão da Produção: Comprometimento"),
    ("gest_40",  "Gestão da Produção: Resultados"),
    ("amb_41",   "Engenharia Ambiental: Inovação"),
    ("amb_42",   "Engenharia Ambiental: Novas situações"),
    ("seg_43",   "Segurança: Incertezas"),
    ("seg_44",   "Segurança: Decisão"),
    ("lab_45",   "Laboratório: Criatividade"),
    ("lab_46",   "Laboratório: Relacionamento"),
    ("est_47",   "Estágio: Autocontrole emocional"),
    ("est_48",   "Estágio: Capacidade empreendedora"),
    ("bio_49",   "Biotecnologia: Dados"),
    ("bio_50",   "Biotecnologia: Ferramentas"),
    ("petro_51", "Petróleo: Recuperação"),
    ("petro_52", "Petróleo: Reatores"),
    ("poli_53",  "Polímeros: Cinética"),
    ("poli_54",  "Polímeros: Produtos"),
    ("cat_55",   "Catálise: Mecanismos de transformação"),
    ("cat_56",   "Catálise: Aplicar na produção"),
    ("sim_57",   "Simulação: Dados"),
    ("sim_58",   "Simulação: Comunicação"),
    ("otim_59",  "Otimização: Soluções"),
    ("otim_60",  "Otimização: Modelos"),
    ("tcc_61",   "TCC: Comunicação"),
    ("tcc_62",   "TCC: Liderança"),
    ("q20_indiv","Capacidade de aprender rapidamente novos conceitos (Geral)")
]

ID_PARA_LABEL = {id_: f"Questão {i+1}" for i, (id_, _) in enumerate(ORDEM_QUESTOES)}
ID_PARA_TEXTO = {id_: titulo for (id_, titulo) in ORDEM_QUESTOES}

def dataframe_ordenado_para_visual(df: pd.DataFrame):
    ids_presentes = [id_ for id_, _ in ORDEM_QUESTOES if id_ in df.columns]
    if not ids_presentes:
        return pd.DataFrame(), []
    df_nums = df[ids_presentes].apply(pd.to_numeric, errors='coerce')
    labels_ordem = [ID_PARA_LABEL[id_] for id_ in ids_presentes]
    textos_ordem = [ID_PARA_TEXTO[id_] for id_ in ids_presentes]
    df_nums.columns = labels_ordem
    mapa = list(zip(labels_ordem, textos_ordem))
    return df_nums, mapa

# ==============================================================================
# 7) BARRA LATERAL (COM EXPANDER PARA O MANUAL)
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ MODO DE OPERAÇÃO")
    modo_operacao = st.radio("Selecione:", ["📝 Nova Transcrição", "✏️ Editar Registro", "📊 Painel Gerencial"], label_visibility="collapsed")
    st.markdown("---")
    
    if modo_operacao == "📝 Nova Transcrição":
        st.markdown("#### 👤 Identificação")
        st.info("Preencha conforme o papel.")
        k_sfx = f"_{st.session_state.form_key}"
        st.selectbox("Responsável", LISTA_PETIANOS, key=f"ident_pet{k_sfx}")
        st.text_input("Nome do Discente", key=f"ident_nome{k_sfx}")
        st.text_input("Matrícula", key=f"ident_mat{k_sfx}")
        st.selectbox("Semestre", LISTA_SEMESTRES, key=f"ident_sem{k_sfx}")
        st.radio("Matriz", LISTA_CURRICULOS, key=f"ident_curr{k_sfx}")
        
        if st.button("Limpar Formulário", icon=":material/delete:"): 
            limpar_formulario()
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📘 Ver Manual de Procedimentos", expanded=False):
            st.caption("A fidelidade aos dados é a prioridade absoluta.")
            st.markdown("* **Não altere erros:** Transcreva exatamente o que vê (ipsis litteris).\n* **Letra Ilegível:** Digite `[ILEGÍVEL]`.")
            st.markdown("* **N/A (Não se Aplica):** Use quando vazio/rasura/duplicado.\n* **Nota:** N/A não entra na média.")
            st.error("O sistema **BLOQUEIA** o salvamento se a Reflexão Final estiver vazia (use **EM BRANCO**).")

# ==============================================================================
# 8) NOVA TRANSCRIÇÃO
# ==============================================================================
if modo_operacao == "📝 Nova Transcrição":
    secao_ativa = st.radio("Etapas:", SECOES, horizontal=True, key="nav_etapa", label_visibility="collapsed")
    st.markdown("---")
    k_suffix = f"_{st.session_state.form_key}"

    def bloco_avancar(key):
        st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("SALVAR RASCUNHO E AVANÇAR", icon=":material/arrow_forward:", on_click=navegar_proxima, key=key)
        st.markdown('</div>', unsafe_allow_html=True)

    if secao_ativa == SECOES[0]:
        st.markdown("### 1. COMPETÊNCIAS TÉCNICAS E GERAIS")
        for id_, titulo in ORDEM_QUESTOES[:8]: renderizar_pergunta(f"{ID_PARA_LABEL[id_]} — {titulo}", id_, key_suffix=k_suffix)
        st.markdown("---"); bloco_avancar("btn_nav1")

    elif secao_ativa == SECOES[1]:
        st.markdown("### 2. COMPETÊNCIAS ESPECÍFICAS")
        for id_, titulo in ORDEM_QUESTOES[8:19]: renderizar_pergunta(f"{ID_PARA_LABEL[id_]} — {titulo}", id_, key_suffix=k_suffix)
        st.markdown("---"); bloco_avancar("btn_nav2")

    elif secao_ativa == SECOES[2]:
        st.markdown("### 3. DISCIPLINAS BÁSICAS")
        for id_, titulo in ORDEM_QUESTOES[19:31]: renderizar_pergunta(f"{ID_PARA_LABEL[id_]} — {titulo}", id_, key_suffix=k_suffix)
        st.markdown("---"); bloco_avancar("btn_nav3")

    elif secao_ativa == SECOES[3]:
        st.markdown("### 4. DISCIPLINAS PROFISSIONALIZANTES")
        for id_, titulo in ORDEM_QUESTOES[31:41]: renderizar_pergunta(f"{ID_PARA_LABEL[id_]} — {titulo}", id_, key_suffix=k_suffix)
        st.markdown("---"); bloco_avancar("btn_nav4")

    elif secao_ativa == SECOES[4]:
        st.markdown("### 5. DISCIPLINAS AVANÇADAS")
        for id_, titulo in ORDEM_QUESTOES[41:-1]: renderizar_pergunta(f"{ID_PARA_LABEL[id_]} — {titulo}", id_, key_suffix=k_suffix)
        st.markdown("---"); bloco_avancar("btn_nav5")

    elif secao_ativa == SECOES[5]:
        st.markdown("### 6. REFLEXÃO FINAL E AUTOAVALIAÇÃO")
        st.warning("⚠️ Obrigatório. Se o físico estiver vazio, digite 'EM BRANCO'.")
        id20, tit20 = ORDEM_QUESTOES[-1]
        renderizar_pergunta(f"{ID_PARA_LABEL[id20]} — {tit20}", id20, key_suffix=k_suffix)

        st.markdown("#### TRANSCRIÇÃO DAS RESPOSTAS ABERTAS")
        txt_fortes = st.text_area("Pontos Fortes *", help="Obrigatório.", key=f"obs_fortes{k_suffix}")
        txt_fracos = st.text_area("Pontos a Desenvolver *", help="Obrigatório.", key=f"obs_fracos{k_suffix}")
        txt_prat   = st.text_area("Contribuição Prática", key=f"obs_prat{k_suffix}")
        txt_ex     = st.text_area("Exemplos de Aplicação", key=f"obs_ex{k_suffix}")
        txt_fut1   = st.text_area("Competências Futuras", key=f"obs_fut1{k_suffix}")
        txt_fut2   = st.text_area("Plano de Desenvolvimento", key=f"obs_fut2{k_suffix}")
        txt_final  = st.text_area("Comentários Finais *", help="Obrigatório.", key=f"obs_final{k_suffix}")

        st.markdown("---")
        st.markdown('<div class="botao-final">', unsafe_allow_html=True)
        if st.button("FINALIZAR E SALVAR REGISTRO", type="primary", icon=":material/save:"):
            dados_salvar = {
                "Registro_ID": str(uuid.uuid4()),
                "Petiano_Responsavel": st.session_state.get(f"ident_pet{k_suffix}", ""),
                "Nome": st.session_state.get(f"ident_nome{k_suffix}", ""),
                "Matricula": st.session_state.get(f"ident_mat{k_suffix}", ""),
                "Semestre": st.session_state.get(f"ident_sem{k_suffix}", ""),
                "Curriculo": st.session_state.get(f"ident_curr{k_suffix}", ""),
                "Data_Registro": obter_hora_ceara(),
                "Autoavaliação: Pontos Fortes": (txt_fortes or "").strip(),
                "Autoavaliação: Pontos a Desenvolver": (txt_fracos or "").strip(),
                "Contribuição Prática": (txt_prat or "").strip(),
                "Exemplos de Aplicação": (txt_ex or "").strip(),
                "Competências Futuras": (txt_fut1 or "").strip(),
                "Plano de Desenvolvimento": (txt_fut2 or "").strip(),
                "Observações Finais": (txt_final or "").strip(),
            }
            for k, v in st.session_state.items():
                if k.endswith(k_suffix):
                    if k.startswith("nota_"):
                        col_name = k.replace("nota_", "").replace(k_suffix, "")
                        dados_salvar[col_name] = v
                    elif k.startswith("obs_") and not any(x in k for x in ["fortes","fracos","prat","ex","fut1","fut2","final"]):
                        col_name = "Obs_" + k.replace("obs_", "").replace(k_suffix, "")
                        dados_salvar[col_name] = v

            erros = []
            if not dados_salvar["Nome"]: erros.append("Nome do Discente")
            if not dados_salvar["Petiano_Responsavel"]: erros.append("Petiano Responsável")
            if not dados_salvar["Autoavaliação: Pontos Fortes"]: erros.append("Pontos Fortes (Obrigatório)")
            if not dados_salvar["Autoavaliação: Pontos a Desenvolver"]: erros.append("Pontos a Desenvolver (Obrigatório)")
            if not dados_salvar["Observações Finais"]: erros.append("Comentários Finais (Obrigatório)")

            if erros:
                st.error(f"❌ IMPOSSÍVEL SALVAR: {', '.join(erros)}")
            else:
                try:
                    conn.table("respostas_sac").insert(dados_salvar).execute()
                    st.balloons(); st.success(f"✅ Transcrição de {dados_salvar['Nome']} salva com sucesso no banco de dados!")
                    limpar_formulario(); st.rerun()
                except Exception as e:
                    st.error(f"❌ ERRO ao salvar no banco: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    salvar_estado()

# ==============================================================================
# 9) EDIÇÃO DE REGISTRO
# ==============================================================================
elif modo_operacao == "✏️ Editar Registro":
    st.markdown("### ✏️ MODO DE EDIÇÃO")
    st.markdown("<div class='edit-warning'>⚠️ Atenção: Alterações sobrescrevem permanentemente o registro no banco.</div>", unsafe_allow_html=True)

    df = ler_banco()
    if df.empty:
        st.warning("Banco de dados vazio.")
    else:
        col1, col2 = st.columns([0.5, 0.5])
        termo = col1.text_input("🔎 Buscar por Nome/Matrícula (contém):")
        sems_db = sorted([s for s in df.get('Semestre', pd.Series(dtype=str)).dropna().unique()])
        filtro_sem = col2.selectbox("Filtrar por Semestre:", ["Todos"] + sems_db)

        df_f = df.copy()
        if termo:
            t = termo.lower()
            df_f = df_f[df_f.apply(lambda r: t in str(r.get("Nome","")).lower() or t in str(r.get("Matricula","")).lower(), axis=1)]
        if filtro_sem != "Todos": df_f = df_f[df_f['Semestre'] == filtro_sem]

        if df_f.empty:
            st.info("Sem resultados para os filtros atuais.")
        else:
            opcoes = df_f.apply(lambda x: f"{x.get('Registro_ID','')} • {x.get('Nome','')} ({x.get('Matricula','')})", axis=1).tolist()
            sel = st.selectbox("Selecione o registro para corrigir:", opcoes)
            sel_id = sel.split(" • ")[0].strip()
            
            dados = df[df['Registro_ID'] == sel_id].iloc[0]

            st.subheader("1) Dados Cadastrais")
            c1, c2 = st.columns(2)
            new_nome = c1.text_input("Nome", value=dados.get("Nome", ""))
            new_mat  = c2.text_input("Matrícula", value=dados.get("Matricula", ""))
            val_sem  = dados.get("Semestre", "")
            idx_sem  = LISTA_SEMESTRES.index(val_sem) if val_sem in LISTA_SEMESTRES else 0
            new_sem  = c1.selectbox("Semestre", LISTA_SEMESTRES, index=idx_sem)
            val_curr = dados.get("Curriculo", "")
            idx_curr = LISTA_CURRICULOS.index(val_curr) if val_curr in LISTA_CURRICULOS else 0
            new_curr = c2.radio("Currículo", LISTA_CURRICULOS, index=idx_curr)
            val_pet  = dados.get("Petiano_Responsavel", "")
            idx_pet  = LISTA_PETIANOS.index(val_pet) if val_pet in LISTA_PETIANOS else 0
            new_pet  = st.selectbox("Responsável pela Transcrição", LISTA_PETIANOS, index=idx_pet)

            st.markdown("---")
            st.subheader("2) Corrigir Nota de uma Questão")
            cols_notas_existentes = [id_ for id_, _ in ORDEM_QUESTOES if id_ in df.columns]
            labels_disp = [ID_PARA_LABEL[id_] for id_ in cols_notas_existentes]
            escolha_label = st.selectbox("Questão:", labels_disp)
            col_edit = cols_notas_existentes[labels_disp.index(escolha_label)]

            edit_labels = NOTA_LABELS
            k_edit = "_edit"
            nota_edit_key = f"nota_edit{k_edit}"
            valor_atual = dados.get(col_edit, "N/A")
            if nota_edit_key not in st.session_state or st.session_state[nota_edit_key] not in edit_labels:
                st.session_state[nota_edit_key] = valor_atual if valor_atual in edit_labels else "N/A"
            sel_edit = st.session_state[nota_edit_key]
            
            for lab in edit_labels:
                cb_key = f"cb_edit_{lab}{k_edit}"
                if cb_key not in st.session_state:
                    st.session_state[cb_key] = (lab == sel_edit)
            cols_e = st.columns(len(edit_labels))
            for i, lab in enumerate(edit_labels):
                cb_key = f"cb_edit_{lab}{k_edit}"
                def _cb_edit_change(label_clicked=lab):
                    cur = st.session_state.get(cb_key, False)
                    if cur:
                        st.session_state[nota_edit_key] = label_clicked
                        for L in edit_labels:
                            st.session_state[f"cb_edit_{L}{k_edit}"] = (L == label_clicked)
                    else:
                        current_sel = st.session_state.get(nota_edit_key, "N/A")
                        for L in edit_labels:
                            st.session_state[f"cb_edit_{L}{k_edit}"] = (L == current_sel)
                cols_e[i].checkbox(lab, value=st.session_state.get(cb_key, lab == sel_edit), key=cb_key, on_change=_cb_edit_change)

            st.markdown("---")
            editar_obs = st.checkbox("Editar observações abertas (opcional)")
            if editar_obs:
                st.subheader("3) Observações/Abertas")
                new_fortes = st.text_area("Pontos Fortes", value=dados.get("Autoavaliação: Pontos Fortes", ""))
                new_fracos = st.text_area("Pontos a Desenvolver", value=dados.get("Autoavaliação: Pontos a Desenvolver", ""))
                new_prat   = st.text_area("Contribuição Prática", value=dados.get("Contribuição Prática", ""))
                new_ex     = st.text_area("Exemplos de Aplicação", value=dados.get("Exemplos de Aplicação", ""))
                new_fut1   = st.text_area("Competências Futuras", value=dados.get("Competências Futuras", ""))
                new_fut2   = st.text_area("Plano de Desenvolvimento", value=dados.get("Plano de Desenvolvimento", ""))
                new_final  = st.text_area("Comentários Finais", value=dados.get("Observações Finais", ""))
            else:
                new_fortes = dados.get("Autoavaliação: Pontos Fortes", "")
                new_fracos = dados.get("Autoavaliação: Pontos a Desenvolver", "")
                new_prat   = dados.get("Contribuição Prática", "")
                new_ex     = dados.get("Exemplos de Aplicação", "")
                new_fut1   = dados.get("Competências Futuras", "")
                new_fut2   = dados.get("Plano de Desenvolvimento", "")
                new_final  = dados.get("Observações Finais", "")

            st.markdown("---")
            if st.button("SALVAR ALTERAÇÕES", icon=":material/update:"):
                novos_dados = {
                    "Nome": new_nome,
                    "Matricula": new_mat,
                    "Semestre": new_sem,
                    "Curriculo": new_curr,
                    "Petiano_Responsavel": new_pet,
                    col_edit: st.session_state.get(nota_edit_key, "N/A"),
                    "Autoavaliação: Pontos Fortes": new_fortes,
                    "Autoavaliação: Pontos a Desenvolver": new_fracos,
                    "Contribuição Prática": new_prat,
                    "Exemplos de Aplicação": new_ex,
                    "Competências Futuras": new_fut1,
                    "Plano de Desenvolvimento": new_fut2,
                    "Observações Finais": new_final
                }
                try:
                    conn.table("respostas_sac").update(novos_dados).eq("Registro_ID", sel_id).execute()
                    st.success("Registro atualizado com sucesso no banco de dados!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")

# ==============================================================================
# 10) PAINEL GERENCIAL
# ==============================================================================
elif modo_operacao == "📊 Painel Gerencial":
    st.markdown("### 📊 INDICADORES DE DESEMPENHO")
    df = ler_banco()
    if df.empty:
        st.info("Nenhum dado.")
    else:
        sems_db = sorted(list(df['Semestre'].dropna().unique())) if 'Semestre' in df.columns else []
        filtro_sem = st.sidebar.selectbox("Filtrar por Semestre:", ["Todos"] + sems_db)
        if filtro_sem != "Todos": df = df[df['Semestre'] == filtro_sem]

        df_nums, mapa = dataframe_ordenado_para_visual(df)
        st.markdown("#### 📍 Resumo")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Formulários", len(df))
        if not df_nums.empty:
            todos_valores = df_nums.stack()
            media = todos_valores.mean()
            desvio = todos_valores.std()
            c2.metric("Média Geral (Válidas)", f"{media:.2f}/5.0")
            c3.metric("Desvio Padrão", f"{desvio:.2f}")
            if 'Data_Registro' in df.columns:
                try:
                    last = pd.to_datetime(df['Data_Registro'], errors='coerce').max()
                    c4.metric("Última Atividade", last.strftime("%d/%m %H:%M") if pd.notna(last) else "-")
                except Exception:
                    c4.metric("Última Atividade", "-")
        st.markdown("---")

        st.markdown("#### 📈 Média por Questão (ordem)")
        if not df_nums.empty:
            medias = df_nums.mean().reset_index()
            medias.columns = ["Questão", "Média"]
            desc_map = {q: desc for q, desc in mapa}
            medias["Descrição Completa"] = medias["Questão"].map(desc_map)
            fig = px.bar(
                medias,
                x="Média", y="Questão",
                orientation="h",
                text="Média",
                hover_data={"Questão": True, "Média": True, "Descrição Completa": True},
                labels={"Média": "Média (0–5)", "Questão": ""},
                color="Média",
                color_continuous_scale=[(0, '#cfd8dc'), (0.5, '#dba800'), (1, '#002060')]
            )
            fig.update_layout(
                height=max(420, len(medias) * 26),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                coloraxis_showscale=False
            )
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📋 Tabela (respostas em ordem)")
        if not df_nums.empty:
            id_cols = ["Registro_ID","Nome","Matricula","Semestre","Curriculo","Petiano_Responsavel","Data_Registro"]
            id_cols_presentes = [c for c in id_cols if c in df.columns]
            df_view = pd.concat([df[id_cols_presentes], df_nums], axis=1)
            colA, colB = st.columns(2)
            nome_q = colA.text_input("Filtrar por Nome (contém):", "")
            mat_q  = colB.text_input("Filtrar por Matrícula (contém):", "")
            if nome_q: df_view = df_view[df_view['Nome'].str.contains(nome_q, case=False, na=False)]
            if mat_q:  df_view = df_view[df_view['Matricula'].str.contains(mat_q, case=False, na=False)]
            st.dataframe(df_view, use_container_width=True, height=520)
            
            csv_bytes = df_view.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("Baixar CSV (visualização)", csv_bytes, file_name=f"sac_banco_visual_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", icon=":material/download:")
