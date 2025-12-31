
# app.py
import os
import json
import uuid
from datetime import datetime, timedelta, timezone

import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================================================================
# 1. CONFIGURAÇÕES GERAIS
# ==============================================================================
st.set_page_config(
    page_title="S.A.C. - PET Engenharia Química",
    layout="wide",
    page_icon="📝",
    initial_sidebar_state="expanded",
)

ARQUIVO_DB = "respostas_sac_deq.csv"
ARQUIVO_BACKUP = "_backup_autosave.json"
CSV_ENCODING = "utf-8-sig"   # Amigável para Excel

# ==============================================================================
# 2. ESTILO
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

@media (prefers-color-scheme: dark) {
    h1, h2, h3, h4 { color: #82b1ff !important; }
    .pergunta-card { background-color: #1e1e1e !important; border-left: 5px solid #82b1ff !important; border: 1px solid #333 !important; }
    .manual-box { background-color: #262730 !important; border: 1px solid #444 !important; }
    .edit-warning { background-color: #3e2723 !important; color: #ffcc80 !important; border: 1px solid #ffab91 !important; }
}
@media (prefers-color-scheme: light) {
    .stApp { background-color: #ffffff !important; }
    .pergunta-card { background-color: #fcfcfc !important; border-left: 5px solid #002060 !important; border: 1px solid #e0e0e0 !important; }
    .manual-box { background-color: #f0f2f6 !important; border: 1px solid #ddd !important; }
    .edit-warning { background-color: #fff3e0 !important; color: #e65100 !important; border: 1px solid #ffe0b2 !important; }
}

.pergunta-card {
    border-radius: 8px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.pergunta-texto {
    font-size: 1.1rem; font-weight: 700; margin-bottom: 15px; opacity: 0.95;
}

.stButton button {
    border-radius: 6px; font-weight: 700; text-transform: uppercase; height: 3.5em; width: 100%; transition: all 0.3s ease;
}
.botao-avancar button { background-color: transparent; border: 2px solid #002060; color: #002060; }
.botao-avancar button:hover { background-color: #002060; color: white; transform: translateX(5px); }
.botao-final button { background-color: #002060 !important; color: white !important; border: none; height: 4.5em; font-size: 1.1rem; }
.botao-final button:hover { background-color: #003399 !important; transform: scale(1.02); }

.manual-box { padding: 15px; border-radius: 8px; margin-bottom: 15px; }
.edit-warning { padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
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
# 4. SUPORTE/UTILS
# ==============================================================================
SECOES = ["1. Gerais", "2. Específicas", "3. Básicas", "4. Profissionais", "5. Avançadas", "6. Reflexão"]

LISTA_PETIANOS = sorted(["", "Ana Carolina", "Ana Clara", "Ana Júlia", "Eric Rullian", "Gildelandio Junior", "Lucas Mossmann (trainee)", "Pedro Paulo"])
LISTA_SEMESTRES = [f"{i}º Semestre" for i in range(1, 11)]
LISTA_CURRICULOS = ["Novo (2023.1)", "Antigo (2005.1)", "Troca de Matriz (Velha -> Nova)"]

# Navegação: usar key distinta para evitar o erro de “não modificar key já instanciada”
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

def escrever_csv_atomico(df_final: pd.DataFrame, destino: str, encoding: str = CSV_ENCODING):
    tmp = destino + ".tmp"
    df_final.to_csv(tmp, index=False, encoding=encoding)
    os.replace(tmp, destino)

def ler_csv_seguro(caminho: str) -> pd.DataFrame:
    if not os.path.exists(caminho): return pd.DataFrame()
    for enc in (CSV_ENCODING, "utf-8", "latin-1"):
        try: return pd.read_csv(caminho, dtype=str, encoding=enc)
        except Exception: continue
    return pd.read_csv(caminho, dtype=str)

# Garante que toda linha tenha Registro_ID
def ensure_registro_id(df: pd.DataFrame) -> pd.DataFrame:
    if "Registro_ID" not in df.columns:
        df["Registro_ID"] = [str(uuid.uuid4()) for _ in range(len(df))]
        escrever_csv_atomico(df, ARQUIVO_DB, encoding=CSV_ENCODING)
        return df
    # completar IDs faltantes
    faltantes = df["Registro_ID"].isna() | (df["Registro_ID"].str.strip() == "")
    if faltantes.any():
        df.loc[faltantes, "Registro_ID"] = [str(uuid.uuid4()) for _ in range(faltantes.sum())]
        escrever_csv_atomico(df, ARQUIVO_DB, encoding=CSV_ENCODING)
    return df

# Checkbox exclusivo para N/A, 0..5
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
                    help="Selecione apenas uma opção. Use 'N/A' se vazio."
                )
        with c2:
            st.text_input(
                "Transcrição de Obs.",
                value=str(obs_padrao) if pd.notna(obs_padrao) else "",
                placeholder="Comentários...",
                key=f"obs_{id_unica}{k}"
            )

# Painel — colunas
IGNORAR_PADRAO = {
    'Nome', 'Matricula', 'Semestre', 'Curriculo', 'Data_Registro',
    'Petiano_Responsavel', 'Registro_ID', 'Autoavaliação: Pontos Fortes',
    'Autoavaliação: Pontos a Desenvolver', 'Contribuição Prática', 'Exemplos de Aplicação',
    'Competências Futuras', 'Plano de Desenvolvimento', 'Observações Finais'
}
GRUPOS_ANALISE = {
    "Competências Gerais": ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q20_indiv"],
    "Competências Específicas": [f"q{i}" for i in range(9, 20)],
    "Disciplinas Básicas": ["calc_", "fis_", "qui_", "termo_", "ft_", "mecflu_"],
    "Disciplinas Profissionais": ["op1_", "op2_", "reat_", "ctrl_", "proj_"],
    "Disciplinas Avançadas": ["econ_", "gest_", "amb_", "seg_", "lab_", "est_", "bio_", "petro_", "poli_", "cat_", "sim_", "otim_", "tcc_"]
}
def colunas_nota(df: pd.DataFrame):
    return [c for c in df.columns if c not in IGNORAR_PADRAO and not c.startswith(("Obs_"))]

# ==============================================================================
# 5. BARRA LATERAL
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ MODO DE OPERAÇÃO")
    modo_operacao = st.radio("Selecione:", ["📝 Nova Transcrição", "✏️ Editar Registro", "📊 Painel Gerencial"], label_visibility="collapsed")
    st.markdown("---")
    if modo_operacao == "📝 Nova Transcrição":
        tab_id, tab_manual = st.tabs(["👤 Identificação", "📘 Manual"])
        with tab_id:
            st.info("Preencha conforme o papel.")
            k_sfx = f"_{st.session_state.form_key}"
            st.selectbox("Responsável", LISTA_PETIANOS, key=f"ident_pet{k_sfx}")
            st.text_input("Nome do Discente", key=f"ident_nome{k_sfx}")
            st.text_input("Matrícula", key=f"ident_mat{k_sfx}")
            st.selectbox("Semestre", LISTA_SEMESTRES, key=f"ident_sem{k_sfx}")
            st.radio("Matriz", LISTA_CURRICULOS, key=f"ident_curr{k_sfx}")
            if st.button("🗑️ Limpar Formulário"): limpar_formulario(); st.rerun()
        with tab_manual:
            st.markdown("### 📘 PROCEDIMENTOS PADRÃO")
            with st.expander("1. Preparação e Conduta", expanded=True):
                st.caption("A fidelidade aos dados é a prioridade absoluta.")
                st.markdown("* **Não altere erros:** Transcreva exatamente o que vê (ipsis litteris).\n* **Letra Ilegível:** Digite `[ILEGÍVEL]`.")
            with st.expander("2. Escala Numérica e 'N/A'"):
                st.markdown("* **N/A (Não se Aplica):** Use OBRIGATORIAMENTE quando o campo está em branco/rasura/duplicado.\n* **Nota:** N/A não conta na média.")
            with st.expander("3. Seção Final (Obrigatória)"):
                st.error("O sistema **BLOQUEIA** o salvamento se a Reflexão Final estiver vazia. Use **EM BRANCO** ou **NÃO RESPONDEU**.")

# ==============================================================================
# 6. NOVA TRANSCRIÇÃO
# ==============================================================================
if modo_operacao == "📝 Nova Transcrição":
    secao_ativa = st.radio("Etapas:", SECOES, horizontal=True, key="nav_etapa", label_visibility="collapsed")
    st.markdown("---")
    k_suffix = f"_{st.session_state.form_key}"

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
        st.markdown("---"); st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav1")
        st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[1]:
        st.markdown("### 2. COMPETÊNCIAS ESPECÍFICAS")
        for i, texto in enumerate([
            "9. Aplicar conhecimentos matemáticos, científicos e tecnológicos",
            "10. Compreender e modelar transferência de quantidade de movimento, calor e massa",
            "11. Aplicar conhecimentos de fenômenos de transporte ao projeto",
            "12. Compreender mecanismos de transformação da matéria e energia",
            "13. Projetar sistemas de recuperação, separação e purificação",
            "14. Compreender mecanismos cinéticos de reações químicas",
            "15. Projetar e otimizar sistemas reacionais e reatores",
            "16. Projetar sistemas de controle de processos industriais",
            "17. Projetar e otimizar plantas industriais (ambiental/segurança)",
            "18. Aplicação de conhecimentos em projeto básico e dimensionamento",
            "19. Execução de projetos de produção e melhorias de processos",
        ], start=9):
            renderizar_pergunta(texto, f"q{i}", key_suffix=k_suffix)
        st.markdown("---"); st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav2")
        st.markdown('</div>', unsafe_allow_html=True)

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
        st.markdown("---"); st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav3")
        st.markdown('</div>', unsafe_allow_html=True)

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
        st.markdown("---"); st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav4")
        st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[4]:
        st.markdown("### 5. DISCIPLINAS AVANÇADAS")
        with st.expander("GESTÃO, ECONOMIA E MEIO AMBIENTE", expanded=True):
            for lab, id_ in [
                ("37. Eng. Econômica: Novos conceitos","econ_37"), ("38. Eng. Econômica: Visão global","econ_38"),
                ("39. Gestão Produção: Comprometimento","gest_39"), ("40. Gestão Produção: Resultados","gest_40"),
                ("41. Eng. Ambiental: Inovação","amb_41"), ("42. Eng. Ambiental: Novas situações","amb_42"),
                ("43. Segurança: Incertezas","seg_43"), ("44. Segurança: Decisão","seg_44"),
            ]: renderizar_pergunta(lab, id_, key_suffix=k_suffix)
        with st.expander("ATIVIDADES PRÁTICAS (LABORATÓRIO E ESTÁGIO)", expanded=True):
            for lab, id_ in [
                ("45. Laboratório: Criatividade","lab_45"), ("46. Laboratório: Relacionamento","lab_46"),
                ("47. Estágio: Autocontrole emocional","est_47"), ("48. Estágio: Capacidade empreendedora","est_48"),
            ]: renderizar_pergunta(lab, id_, key_suffix=k_suffix)
        with st.expander("DISCIPLINAS OPTATIVAS E INTEGRADORAS", expanded=True):
            for lab, id_ in [
                ("49. Biotec: Dados","bio_49"), ("50. Biotec: Ferramentas","bio_50"),
                ("51. Petróleo: Recuperação","petro_51"), ("52. Petróleo: Reatores","petro_52"),
                ("53. Polímeros: Cinética","poli_53"), ("54. Polímeros: Produtos","poli_54"),
                ("55. Catálise: Mecanismos de transformação","cat_55"), ("56. Catálise: Aplicar na produção","cat_56"),
                ("57. Simulação: Dados","sim_57"), ("58. Simulação: Comunicação","sim_58"),
                ("59. Otimização: Soluções","otim_59"), ("60. Otimização: Modelos","otim_60"),
                ("61. TCC: Comunicação","tcc_61"), ("62. TCC: Liderança","tcc_62"),
            ]: renderizar_pergunta(lab, id_, key_suffix=k_suffix)
        st.markdown("---"); st.markdown('<div class="botao-avancar">', unsafe_allow_html=True)
        st.button("SALVAR RASCUNHO E AVANÇAR ➡️", on_click=navegar_proxima, key="btn_nav5")
        st.markdown('</div>', unsafe_allow_html=True)

    elif secao_ativa == SECOES[5]:
        st.markdown("### 6. REFLEXÃO FINAL E AUTOAVALIAÇÃO")
        st.warning("⚠️ **ATENÇÃO:** Preenchimento OBRIGATÓRIO. Se vazio no físico, digite 'EM BRANCO'.")
        renderizar_pergunta("20. Capacidade de aprender rapidamente novos conceitos (Geral)", "q20_indiv", key_suffix=k_suffix)

        st.markdown("#### TRANSCRIÇÃO DAS RESPOSTAS ABERTAS")
        txt_fortes = st.text_area("Pontos Fortes *", help="Obrigatório.", key=f"obs_fortes{k_suffix}")
        txt_fracos = st.text_area("Pontos a Desenvolver *", help="Obrigatório.", key=f"obs_fracos{k_suffix}")
        txt_prat = st.text_area("Contribuição Prática", key=f"obs_prat{k_suffix}")
        txt_ex = st.text_area("Exemplos de Aplicação", key=f"obs_ex{k_suffix}")
        txt_fut1 = st.text_area("Competências Futuras", key=f"obs_fut1{k_suffix}")
        txt_fut2 = st.text_area("Plano de Desenvolvimento", key=f"obs_fut2{k_suffix}")
        txt_final = st.text_area("Comentários Finais *", help="Obrigatório.", key=f"obs_final{k_suffix}")

        st.markdown("---")
        st.markdown('<div class="botao-final">', unsafe_allow_html=True)
        if st.button("💾 FINALIZAR E SALVAR REGISTRO", type="primary"):
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
                    elif k.startswith("obs_") and not any(x in k for x in ["fortes", "fracos", "prat", "ex", "fut1", "fut2", "final"]):
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
                    df_new = pd.DataFrame([dados_salvar])
                    df_antigo = ler_csv_seguro(ARQUIVO_DB)
                    if df_antigo.empty:
                        df_final = df_new
                    else:
                        if 'Data_Registro' not in df_antigo.columns:
                            df_antigo['Data_Registro'] = obter_hora_ceara()
                        df_final = pd.concat([df_antigo, df_new], ignore_index=True)
                    escrever_csv_atomico(df_final, ARQUIVO_DB, encoding=CSV_ENCODING)
                    st.balloons(); st.success(f"✅ Transcrição de {dados_salvar['Nome']} salva com sucesso!")
                    limpar_formulario(); st.rerun()
                except PermissionError:
                    st.error("❌ ERRO: Feche o CSV/Excel aberto.")
                except Exception as e:
                    st.error(f"❌ ERRO: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    salvar_estado()

# ==============================================================================
# 7. EDIÇÃO DE REGISTRO (CORRIGIDO)
# ==============================================================================
elif modo_operacao == "✏️ Editar Registro":
    st.markdown("### ✏️ MODO DE EDIÇÃO")
    st.markdown("<div class='edit-warning'>⚠️ Atenção: Alterações sobrescrevem permanentemente o registro.</div>", unsafe_allow_html=True)

    df = ler_csv_seguro(ARQUIVO_DB)
    if df.empty:
        st.warning("Banco de dados vazio.")
    else:
        try:
            df = ensure_registro_id(df)

            # Filtros/busca para localizar fácil
            col1, col2 = st.columns([0.5, 0.5])
            termo = col1.text_input("🔎 Buscar por Nome/Matrícula (contém):")
            sems_db = sorted([s for s in df.get('Semestre', pd.Series(dtype=str)).dropna().unique()])
            filtro_sem = col2.selectbox("Filtrar por Semestre:", ["Todos"] + sems_db)

            df_f = df.copy()
            if termo:
                termo_l = termo.lower()
                df_f = df_f[df_f.apply(lambda r: termo_l in str(r.get("Nome","")).lower() or termo_l in str(r.get("Matricula","")).lower(), axis=1)]
            if filtro_sem != "Todos":
                df_f = df_f[df_f['Semestre'] == filtro_sem]

            if df_f.empty:
                st.info("Sem resultados para os filtros atuais.")
            else:
                # Seleção robusta por Registro_ID
                opcoes = df_f.apply(lambda x: f"{x.get('Registro_ID','')} • {x.get('Nome','')} ({x.get('Matricula','')})", axis=1).tolist()
                sel = st.selectbox("Selecione o registro para corrigir:", opcoes)
                sel_id = sel.split(" • ")[0].strip()
                idx_series = df.index[df['Registro_ID'] == sel_id]
                if len(idx_series) == 0:
                    st.error("Registro não encontrado.")
                else:
                    idx = idx_series[0]
                    dados = df.iloc[idx]

                    with st.form("form_edicao_completa"):
                        st.subheader("1) Dados Cadastrais")
                        c1, c2 = st.columns(2)
                        new_nome = c1.text_input("Nome", value=dados.get("Nome", ""))
                        new_mat = c2.text_input("Matrícula", value=dados.get("Matricula", ""))

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
                        st.subheader("2) Corrigir Nota de uma Competência")
                        cols_notas = colunas_nota(df)
                        col_edit = st.selectbox("Campo de nota para editar:", cols_notas)

                        # Checkboxes exclusivos para a nova nota
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
                            cols_e[i].checkbox(lab, value=st.session_state.get(cb_key, lab == sel_edit), key=cb_key, on_change=_cb_edit_change, help="Selecione apenas uma opção.")

                        st.markdown("---")
                        editar_obs = st.checkbox("Editar campos de observação aberta (opcional)")
                        if editar_obs:
                            st.subheader("3) Observações/Abertas")
                            new_fortes = st.text_area("Pontos Fortes", value=dados.get("Autoavaliação: Pontos Fortes", ""))
                            new_fracos = st.text_area("Pontos a Desenvolver", value=dados.get("Autoavaliação: Pontos a Desenvolver", ""))
                            new_final = st.text_area("Comentários Finais", value=dados.get("Observações Finais", ""))
                        else:
                            new_fortes = dados.get("Autoavaliação: Pontos Fortes", "")
                            new_fracos = dados.get("Autoavaliação: Pontos a Desenvolver", "")
                            new_final = dados.get("Observações Finais", "")

                        st.markdown("---")
                        if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                            df.at[idx, "Nome"] = new_nome
                            df.at[idx, "Matricula"] = new_mat
                            df.at[idx, "Semestre"] = new_sem
                            df.at[idx, "Curriculo"] = new_curr
                            df.at[idx, "Petiano_Responsavel"] = new_pet
                            df.at[idx, col_edit] = st.session_state.get(nota_edit_key, "N/A")
                            df.at[idx, "Autoavaliação: Pontos Fortes"] = new_fortes
                            df.at[idx, "Autoavaliação: Pontos a Desenvolver"] = new_fracos
                            df.at[idx, "Observações Finais"] = new_final
                            escrever_csv_atomico(df, ARQUIVO_DB, encoding=CSV_ENCODING)
                            st.success("Registro atualizado com sucesso!"); st.rerun()

        except Exception as e:
            st.error(f"Erro: {e}")

# ==============================================================================
# 8. PAINEL GERENCIAL (ABAS ORGANIZADAS)
# ==============================================================================
elif modo_operacao == "📊 Painel Gerencial":
    st.markdown("### 📊 INDICADORES DE DESEMPENHO")
    df = ler_csv_seguro(ARQUIVO_DB)
    if df.empty:
        st.info("Nenhum dado.")
    else:
        df = ensure_registro_id(df)
        # Filtros gerais
        sems_db = sorted(list(df['Semestre'].dropna().unique())) if 'Semestre' in df.columns else []
        filtro_sem = st.sidebar.selectbox("Filtrar por Semestre:", ["Todos"] + sems_db)
        if filtro_sem != "Todos": df = df[df['Semestre'] == filtro_sem]

        # Abas: Resumo | Blocos | Ranking | Tabela
        tab_resumo, tab_blocos, tab_ranking, tab_tabela = st.tabs(["📍 Resumo", "🧩 Blocos", "🏆 Ranking", "📋 Tabela"])

        cols_notas = colunas_nota(df)
        df_nums = df[cols_notas].apply(pd.to_numeric, errors='coerce') if cols_notas else pd.DataFrame()

        # --- RESUMO ---
        with tab_resumo:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Formulários", len(df))
            if not df_nums.empty:
                todos_valores = df_nums.stack()
                media = todos_valores.mean()
                desvio = todos_valores.std()
                c2.metric("Média Geral (Válidas)", f"{media:.2f}/5.0")
                c3.metric("Desvio Padrão", f"{desvio:.2f}")
                # Distribuição de notas (0..5), ignorando NaN
                dist = todos_valores.dropna().value_counts().sort_index()
                fig_dist = px.bar(
                    x=dist.index.astype(str), y=dist.values, text=dist.values,
                    labels={'x': 'Nota', 'y': 'Frequência'},
                    color=dist.index, color_continuous_scale=['#cfd8dc','#002060']
                )
                fig_dist.update_layout(title="Distribuição de Notas (0..5)", xaxis_title="Nota", yaxis_title="Frequência", coloraxis_showscale=False)
                st.plotly_chart(fig_dist, use_container_width=True)
            if 'Data_Registro' in df.columns:
                try:
                    last = pd.to_datetime(df['Data_Registro'], errors='coerce').max()
                    c4.metric("Última Atividade", last.strftime("%d/%m %H:%M") if pd.notna(last) else "-")
                except Exception: c4.metric("Última Atividade", "-")

        # --- BLOCOS ---
        with tab_blocos:
            st.markdown("#### Médias por Bloco de Competência")
            for titulo_grupo, chaves in GRUPOS_ANALISE.items():
                cols_grupo = [c for c in cols_notas if any((c == k) or c.startswith(k) for k in chaves)]
                if not cols_grupo: continue
                df_grupo = df[cols_grupo].apply(pd.to_numeric, errors='coerce')
                medias_grupo = df_grupo.mean().sort_values(ascending=True)
                if medias_grupo.empty: continue
                fig = px.bar(
                    medias_grupo,
                    orientation='h',
                    x=medias_grupo.values,
                    y=medias_grupo.index,
                    text_auto='.2f',
                    labels={'index': 'Competência', 'x': 'Média'},
                    color=medias_grupo.values,
                    color_continuous_scale=[(0, '#cfd8dc'), (0.5, '#dba800'), (1, '#002060')]
                )
                fig.update_layout(height=max(300, len(medias_grupo) * 26), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

        # --- RANKING ---
        with tab_ranking:
            st.markdown("#### Top/Bottom Competências (Média)")
            if not df_nums.empty:
                medias_todas = df_nums.mean().sort_values(ascending=False)
                top_n = st.slider("Mostrar Top N:", 5, min(20, len(medias_todas)), 10)
                colA, colB = st.columns(2)
                colA.subheader("🏆 Top")
                colA.dataframe(medias_todas.head(top_n).to_frame("Média"), use_container_width=True, height=300)
                colB.subheader("🔻 Bottom")
                colB.dataframe(medias_todas.tail(top_n).sort_values(ascending=True).to_frame("Média"), use_container_width=True, height=300)
            else:
                st.info("Sem colunas de nota para calcular ranking.")

        # --- TABELA ---
        with tab_tabela:
            st.markdown("#### Tabela Completa (com filtros)")
            # Filtros adicionais
            nome_q = st.text_input("Filtrar por Nome (contém):", "")
            mat_q = st.text_input("Filtrar por Matrícula (contém):", "")
            df_view = df.copy()
            if nome_q: df_view = df_view[df_view['Nome'].str.contains(nome_q, case=False, na=False)]
            if mat_q: df_view = df_view[df_view['Matricula'].str.contains(mat_q, case=False, na=False)]
            ordenar_por = st.selectbox("Ordenar por:", ["Data_Registro","Nome","Semestre","Matricula"], index=0)
            asc = st.checkbox("Ordem crescente", value=False)
            if ordenar_por in df_view.columns:
                df_view = df_view.sort_values(ordenar_por, ascending=asc, na_position='last')

            st.dataframe(df_view, use_container_width=True, height=500)
            csv_bytes = df_view.to_csv(index=False, encoding=CSV_ENCODING).encode(CSV_ENCODING)
            st.download_button("📥 Baixar CSV (filtro aplicado)", csv_bytes, file_name=f"sac_backup_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
