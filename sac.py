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
# 2. ESTILO VISUAL (ALTO CONTRASTE - DATA ENTRY)
# ==============================================================================
st.markdown("""
    <style>
    /* OTIMIZADO PARA DIGITAÇÃO RÁPIDA (Fundo Claro) */
    .stApp { background-color: #ffffff !important; }
    
    /* Texto sempre escuro para leitura fácil */
    p, label, span, div, li, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #2c3e50 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Títulos em Azul Institucional */
    h1, h2, h3 { color: #002060 !important; font-weight: 800; text-transform: uppercase; }

    /* Cabeçalho */
    .header-institucional {
        border-bottom: 4px solid #002060;
        padding-bottom: 15px;
        margin-bottom: 20px;
        text-align: center;
    }

    /* Cards de Pergunta Compactos (Para caber mais na tela) */
    .pergunta-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-left: 5px solid #002060;
        border-radius: 4px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .pergunta-texto {
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 5px;
    }

    /* Botão de Salvar (Destaque) */
    div.stButton > button {
        background-color: #002060 !important;
        color: white !important;
        font-weight: bold;
        text-transform: uppercase;
        height: 3.5em;
        width: 100%;
        border-radius: 6px;
        border: none;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        background-color: #003399 !important;
        transform: scale(1.01);
    }
    div.stButton > button p { color: white !important; }

    /* Inputs */
    input, textarea { border: 1px solid #ccc; border-radius: 4px; }
    input:focus, textarea:focus { border-color: #002060; outline: 2px solid rgba(0,32,96,0.2); }

    /* Menus */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CABEÇALHO
# ==============================================================================
st.markdown("""
    <div class="header-institucional">
        <h1 style="font-size: 2.2rem; margin:0;">S.A.C.</h1>
        <div style="font-weight:600; font-size:1.1rem; color:#555;">SISTEMA DE AVALIAÇÃO CURRICULAR - DIGITAÇÃO</div>
        <div style="font-size:0.85rem; color:#777;">PET ENGENHARIA QUÍMICA - UFC</div>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LÓGICA DE GERENCIAMENTO
# ==============================================================================
if 'form_key' not in st.session_state:
    st.session_state.form_key = 0

def obter_hora_ceara():
    """Garante registro no horário de Fortaleza (UTC-3)."""
    fuso = timezone(timedelta(hours=-3))
    return datetime.now(fuso).strftime("%Y-%m-%d %H:%M:%S")

def limpar_formulario():
    st.session_state.form_key += 1
    if os.path.exists(ARQUIVO_BACKUP):
        try: os.remove(ARQUIVO_BACKUP)
        except: pass

def renderizar_pergunta(texto_pergunta, id_unica):
    with st.container():
        st.markdown(f"""<div class="pergunta-card"><div class="pergunta-texto">{texto_pergunta}</div></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            val = st.select_slider(
                "Nota (0-5)", 
                options=["0", "1", "2", "3", "4", "5"], 
                value="0", 
                key=f"nota_{id_unica}_{st.session_state.form_key}"
            )
        with c2:
            obs = st.text_input(
                "Observação (Transcrição)", 
                placeholder="Transcreva o comentário do papel...", 
                key=f"obs_{id_unica}_{st.session_state.form_key}"
            )
    return int(val), obs

# ==============================================================================
# 5. BARRA LATERAL (IDENTIFICAÇÃO E GUIA DE TRANSCRIÇÃO)
# ==============================================================================
respostas = {}

with st.sidebar:
    tab_form, tab_guia = st.tabs(["👤 Identificação", "📘 Manual de Transcrição"])
    
    # --- ABA 1: IDENTIFICAÇÃO DO FORMULÁRIO ---
    with tab_form:
        st.info("Preencha com os dados do Formulário Físico.")
        
        lista_petianos = [
            "",
            "Ana Carolina",
            "Ana Clara", 
            "Ana Júlia",
            "Eric Rullian", 
            "Gildelandio Junior", 
            "Lucas Mossmann (trainee)",
            "Pedro Paulo"
        ]
        
        respostas["Petiano_Responsavel"] = st.selectbox(
            "Quem está digitando?", 
            lista_petianos,
            key=f"pet_{st.session_state.form_key}"
        )
        
        respostas["Nome"] = st.text_input("Nome do Aluno (Papel)", key=f"nome_{st.session_state.form_key}")
        respostas["Matricula"] = st.text_input("Matrícula (Papel)", key=f"mat_{st.session_state.form_key}")
        
        lista_semestres = [f"{i}º Semestre" for i in range(1, 11)]
        respostas["Semestre"] = st.selectbox("Semestre Marcado", lista_semestres, key=f"sem_{st.session_state.form_key}")
        
        respostas["Curriculo"] = st.radio(
            "Currículo Marcado", 
            ["Novo (2023.1)", "Antigo (2005.1)"], 
            key=f"curr_{st.session_state.form_key}"
        )
        
        respostas["Data_Registro"] = obter_hora_ceara()
        
        st.markdown("---")
        st.caption(f"Registro: {respostas['Data_Registro']}")

    # --- ABA 2: GUIA PASSO A PASSO PARA PETIANOS ---
    with tab_guia:
        st.markdown("### 📘 PROCEDIMENTO DE DIGITAÇÃO")
        st.warning("Atenção: A fidelidade aos dados do papel é essencial.")
        
        st.markdown("#### 1. PREPARAÇÃO")
        st.markdown("""
        1. Separe o bloco de formulários preenchidos.
        2. Selecione seu nome em **'Quem está digitando?'**.
        3. Copie o **Nome** e **Matrícula** exatamente como está no papel.
        """)
        
        st.markdown("#### 2. TRANSCRIÇÃO DAS NOTAS")
        st.markdown("""
        * **Marcou X no 3?** Arraste o slider para o 3.
        * **Não marcou nada?** Mantenha o slider no 0 e escreva *"Em branco"* na observação.
        * **Marcou duas opções?** Considere a maior nota ou consulte o coordenador.
        """)
        
        st.markdown("#### 3. TEXTOS E OBSERVAÇÕES")
        st.markdown("""
        * Digite os comentários **ipsis litteris** (exatamente como escrito).
        * Se a letra estiver ilegível, digite: *"[Ilegível]"*.
        * Se o campo de texto estiver vazio no papel, deixe vazio no sistema.
        """)
        
        st.markdown("#### 4. SEÇÃO FINAL (OBRIGATÓRIA)")
        st.error("""
        **IMPORTANTE:** A última seção (Reflexão) não pode ser salva em branco.
        * Se o aluno escreveu: Transcreva.
        * Se o aluno deixou em branco: Digite **"Não respondeu"** ou **"Em branco"** nos campos.
        """)

# ==============================================================================
# 6. NAVEGAÇÃO E CONTEÚDO
# ==============================================================================

abas = [
    "1. Gerais", 
    "2. Específicas", 
    "3. Básicas", 
    "4. Profissionais", 
    "5. Avançadas", 
    "6. Reflexão (Obrigatória)", 
    "📊 Painel"
]
tabs = st.tabs(abas)

# --- SEÇÃO 1: GERAIS ---
with tabs[0]:
    st.markdown("### 1. COMPETÊNCIAS GERAIS")
    respostas["1. Investigação"], respostas["Obs_1"] = renderizar_pergunta("1. Projetar e conduzir experimentos", "q1")
    respostas["2. Ferramentas"], respostas["Obs_2"] = renderizar_pergunta("2. Desenvolver/utilizar novas ferramentas", "q2")
    respostas["3. Concepção"], respostas["Obs_3"] = renderizar_pergunta("3. Conceber e projetar sistemas", "q3")
    respostas["4. Resolução Prob."], respostas["Obs_4"] = renderizar_pergunta("4. Soluções para problemas de engenharia", "q4")
    respostas["5. Modelagem"], respostas["Obs_5"] = renderizar_pergunta("5. Compreender fenômenos via modelos", "q5")
    respostas["6. Comunicação"], respostas["Obs_6"] = renderizar_pergunta("6. Comunicação escrita, oral e gráfica", "q6")
    respostas["7. Equipe"], respostas["Obs_7"] = renderizar_pergunta("7. Trabalhar e liderar equipes", "q7")
    respostas["8. Ética"], respostas["Obs_8"] = renderizar_pergunta("8. Ética e legislação profissional", "q8")

# --- SEÇÃO 2: ESPECÍFICAS ---
with tabs[1]:
    st.markdown("### 2. COMPETÊNCIAS ESPECÍFICAS")
    respostas["9. Fundamentos Mat."], respostas["Obs_9"] = renderizar_pergunta("9. Aplicar matemática/ciência/tecnologia", "q9")
    respostas["10. Modelagem Transp."], respostas["Obs_10"] = renderizar_pergunta("10. Modelar transf. de movimento, calor e massa", "q10")
    respostas["11. Aplic. Transp."], respostas["Obs_11"] = renderizar_pergunta("11. Aplicar fenômenos de transporte ao projeto", "q11")
    respostas["12. Transf. Matéria"], respostas["Obs_12"] = renderizar_pergunta("12. Mecanismos de transf. matéria e energia", "q12")
    respostas["13. Separação"], respostas["Obs_13"] = renderizar_pergunta("13. Projetar sistemas de separação/purificação", "q13")
    respostas["14. Cinética"], respostas["Obs_14"] = renderizar_pergunta("14. Mecanismos cinéticos de reações", "q14")
    respostas["15. Reatores"], respostas["Obs_15"] = renderizar_pergunta("15. Projetar/otimizar reatores químicos", "q15")
    respostas["16. Controle"], respostas["Obs_16"] = renderizar_pergunta("16. Projetar controle de processos", "q16")
    respostas["17. Projetos Ind."], respostas["Obs_17"] = renderizar_pergunta("17. Projetar plantas industriais (segurança/amb.)", "q17")
    st.markdown("#### Eixos Práticos")
    respostas["18. Projeto Básico"], respostas["Obs_18"] = renderizar_pergunta("18. Projeto básico e dimensionamento", "q18")
    respostas["19. Melhoria Proc."], respostas["Obs_19"] = renderizar_pergunta("19. Execução/Melhoria de processos", "q19")

# --- SEÇÃO 3: BÁSICAS ---
with tabs[2]:
    st.markdown("### 3. DISCIPLINAS BÁSICAS")
    with st.expander("CÁLCULO E FÍSICA"):
        respostas["Cálculo: Dados"], respostas["Obs_C1"] = renderizar_pergunta("21. Analisar grandes volumes de dados", "calc_21")
        respostas["Cálculo: Formação"], respostas["Obs_C2"] = renderizar_pergunta("52. Formação Básica", "calc_52")
        respostas["Física: Operação"], respostas["Obs_F1"] = renderizar_pergunta("22. Analisar operação de sistemas", "fis_22")
        respostas["Física: Ciência"], respostas["Obs_F2"] = renderizar_pergunta("53. Ciência da Engenharia", "fis_53")
    with st.expander("QUÍMICA E TERMO"):
        respostas["Química: Transf."], respostas["Obs_Q1"] = renderizar_pergunta("23. Conhecimentos de transformação", "qui_23")
        respostas["Química: Desenv."], respostas["Obs_Q2"] = renderizar_pergunta("24. Conceber produtos e processos", "qui_24")
        respostas["Termo: Energia"], respostas["Obs_T1"] = renderizar_pergunta("25. Projetar sistemas energéticos", "termo_25")
        respostas["Termo: Ciência"], respostas["Obs_T2"] = renderizar_pergunta("54. Ciência da Eng. Química", "termo_54")
    with st.expander("FENÔMENOS"):
        respostas["FT: Aplicação"], respostas["Obs_FT1"] = renderizar_pergunta("26. Aplicar fenômenos de transporte", "ft_26")
        respostas["FT: Gráficos"], respostas["Obs_FT2"] = renderizar_pergunta("27. Comunicar-se tecnicamente (gráficos)", "ft_27")
        respostas["MecFlu: Soluções"], respostas["Obs_MF1"] = renderizar_pergunta("28. Implantar soluções de engenharia", "mecflu_28")
        respostas["MecFlu: Supervisão"], respostas["Obs_MF2"] = renderizar_pergunta("29. Operar/supervisionar instalações", "mecflu_29")

# --- SEÇÃO 4: PROFISSIONAIS ---
with tabs[3]:
    st.markdown("### 4. DISCIPLINAS PROFISSIONAIS")
    with st.expander("OPERAÇÕES UNITÁRIAS"):
        respostas["OpUnit: Manutenção"], respostas["Obs_O1"] = renderizar_pergunta("30. Inspecionar manutenção", "op1_30")
        respostas["OpUnit: Tecnologia"], respostas["Obs_O1b"] = renderizar_pergunta("55. Tecnologia Industrial", "op1_55")
        respostas["OpUnit: Impacto"], respostas["Obs_O2"] = renderizar_pergunta("31. Estudos de impactos ambientais", "op2_31")
        respostas["OpUnit: Tratamento"], respostas["Obs_O2b"] = renderizar_pergunta("32. Projetar tratamento ambiental", "op2_32")
    with st.expander("REATORES E CONTROLE"):
        respostas["Reatores: Recursos"], respostas["Obs_R1"] = renderizar_pergunta("33. Gerir recursos estratégicos", "reat_33")
        respostas["Reatores: Qualidade"], respostas["Obs_R2"] = renderizar_pergunta("34. Modelos de produção/qualidade", "reat_34")
        respostas["Controle: Supervisão"], respostas["Obs_Ct1"] = renderizar_pergunta("35. Controle/supervisão de instalações", "ctrl_35")
        respostas["Controle: Gestão"], respostas["Obs_Ct2"] = renderizar_pergunta("36. Gestão de empreendimentos", "ctrl_36")
    with st.expander("PROJETOS"):
        respostas["Projetos: Gestão"], respostas["Obs_Pr1"] = renderizar_pergunta("56. Projetos Industriais e Gestão", "proj_56")
        respostas["Projetos: Ética"], respostas["Obs_Pr2"] = renderizar_pergunta("57. Ética e Humanidades", "proj_57")

# --- SEÇÃO 5: AVANÇADAS ---
with tabs[4]:
    st.markdown("### 5. AVANÇADAS E COMPLEMENTARES")
    with st.expander("GESTÃO/AMBIENTAL/SEGURANÇA"):
        respostas["Econ: Novos"], respostas["Obs_Ec1"] = renderizar_pergunta("37. Eng. Econ: Aprender novos conceitos", "econ_37")
        respostas["Econ: Visão"], respostas["Obs_Ec2"] = renderizar_pergunta("38. Eng. Econ: Visão global", "econ_38")
        respostas["Gestão: Compr."], respostas["Obs_G1"] = renderizar_pergunta("39. Gestão: Comprometimento", "gest_39")
        respostas["Gestão: Result."], respostas["Obs_G2"] = renderizar_pergunta("40. Gestão: Resultados efetivos", "gest_40")
        respostas["Amb: Inovação"], respostas["Obs_A1"] = renderizar_pergunta("41. Eng. Amb: Inovação", "amb_41")
        respostas["Amb: Situações"], respostas["Obs_A2"] = renderizar_pergunta("42. Eng. Amb: Situações novas", "amb_42")
        respostas["Seg: Incertezas"], respostas["Obs_S1"] = renderizar_pergunta("43. Segurança: Lidar com incertezas", "seg_43")
        respostas["Seg: Decisão"], respostas["Obs_S2"] = renderizar_pergunta("44. Segurança: Iniciativa e decisão", "seg_44")
    with st.expander("PRÁTICAS (LAB/ESTÁGIO)"):
        respostas["Lab: Criatividade"], respostas["Obs_L1"] = renderizar_pergunta("45. Lab: Criatividade", "lab_45")
        respostas["Lab: Relacionam."], respostas["Obs_L2"] = renderizar_pergunta("46. Lab: Relacionamento interpessoal", "lab_46")
        respostas["Estágio: Autocont."], respostas["Obs_E1"] = renderizar_pergunta("47. Estágio: Autocontrole emocional", "est_47")
        respostas["Estágio: Empreend."], respostas["Obs_E2"] = renderizar_pergunta("48. Estágio: Capacidade empreendedora", "est_48")
    with st.expander("OPTATIVAS E INTEGRADORAS"):
        respostas["Bio: Dados"], respostas["Obs_B1"] = renderizar_pergunta("49. Biotec: Analisar grandes dados", "bio_49")
        respostas["Bio: Ferram."], respostas["Obs_B2"] = renderizar_pergunta("50. Biotec: Novas ferramentas", "bio_50")
        respostas["Petro: Recuper."], respostas["Obs_P1"] = renderizar_pergunta("51. Petróleo: Projetar recuperação", "petro_51")
        respostas["Petro: Reatores"], respostas["Obs_P2"] = renderizar_pergunta("52. Petróleo: Projetar reatores", "petro_52")
        respostas["Poli: Cinética"], respostas["Obs_Po1"] = renderizar_pergunta("53. Polímeros: Mecanismos cinéticos", "poli_53")
        respostas["Poli: Produtos"], respostas["Obs_Po2"] = renderizar_pergunta("54. Polímeros: Conceber produtos", "poli_54")
        respostas["Cat: Mecanismos"], respostas["Obs_Ca1"] = renderizar_pergunta("55. Catálise: Mecanismos transform.", "cat_55")
        respostas["Cat: Produção"], respostas["Obs_Ca2"] = renderizar_pergunta("56. Catálise: Aplicar na produção", "cat_56")
        respostas["Sim: Dados"], respostas["Obs_Si1"] = renderizar_pergunta("57. Simulação: Analisar dados", "sim_57")
        respostas["Sim: Comun."], respostas["Obs_Si2"] = renderizar_pergunta("58. Simulação: Comunicação técnica", "sim_58")
        respostas["Otim: Soluções"], respostas["Obs_Ot1"] = renderizar_pergunta("59. Otimização: Soluções problemas", "otim_59")
        respostas["Otim: Modelos"], respostas["Obs_Ot2"] = renderizar_pergunta("60. Otimização: Modelos produção", "otim_60")
        respostas["TCC: Comun."], respostas["Obs_Tc1"] = renderizar_pergunta("61. TCC: Comunicação escrita/oral", "tcc_61")
        respostas["TCC: Liderança"], respostas["Obs_Tc2"] = renderizar_pergunta("62. TCC: Liderar equipes", "tcc_62")

# --- SEÇÃO 6: REFLEXÃO FINAL (OBRIGATÓRIA) ---
with tabs[5]:
    st.markdown("### 6. REFLEXÃO FINAL E AUTOAVALIAÇÃO")
    st.warning("⚠️ Esta seção é OBRIGATÓRIA para finalizar o cadastro.")
    st.info("Caso o aluno tenha deixado em branco, digite 'Não respondeu'.")
    
    respostas["20. Capacidade de Aprendizado"], respostas["Obs_20"] = renderizar_pergunta("20. Capacidade de aprender rapidamente novos conceitos (Geral)", "q20_indiv")
    
    st.markdown("#### TRANSCRIÇÃO DAS RESPOSTAS ABERTAS")
    
    respostas["Autoavaliação: Pontos Fortes"] = st.text_area("Pontos Fortes (Obrigatório)", key=f"fortes_{st.session_state.form_key}")
    respostas["Autoavaliação: Pontos a Desenvolver"] = st.text_area("Pontos a Desenvolver (Obrigatório)", key=f"fracos_{st.session_state.form_key}")
    
    respostas["Contribuição Prática"] = st.text_area("Contribuição das atividades", key=f"prat_{st.session_state.form_key}")
    respostas["Exemplos de Aplicação"] = st.text_area("Exemplos de aplicação", key=f"ex_{st.session_state.form_key}")
    respostas["Competências Futuras"] = st.text_area("Competências essenciais futuras", key=f"fut1_{st.session_state.form_key}")
    respostas["Plano de Desenvolvimento"] = st.text_area("Plano de desenvolvimento", key=f"fut2_{st.session_state.form_key}")
    respostas["Observações Finais"] = st.text_area("Comentários Finais", key=f"obsf_{st.session_state.form_key}")

    st.markdown("---")
    
    # --- LÓGICA DE SALVAMENTO COM VALIDAÇÃO ---
    if st.button("💾 SALVAR E INICIAR PRÓXIMO ALUNO", type="primary"):
        erro = False
        msg = []

        if not respostas["Nome"]:
            erro = True; msg.append("Nome do Discente")
        if not respostas["Petiano_Responsavel"]:
            erro = True; msg.append("Petiano Responsável")
        
        # VALIDAÇÃO DE OBRIGATORIEDADE DA SEÇÃO 6
        if not respostas["Autoavaliação: Pontos Fortes"] or not respostas["Autoavaliação: Pontos a Desenvolver"]:
            st.error("❌ ERRO DE TRANSCRIÇÃO: Os campos de 'Pontos Fortes' e 'Pontos a Desenvolver' não podem ficar vazios.")
            st.warning("👉 Se o papel está em branco, digite 'Não respondeu' ou 'Em branco'.")
            erro = True # Bloqueia o salvamento

        if erro and not (not respostas["Autoavaliação: Pontos Fortes"]): # Se o erro for só nome/petiano
             if not respostas["Nome"] or not respostas["Petiano_Responsavel"]:
                st.error(f"⚠️ Preencha os campos obrigatórios na lateral: {', '.join(msg)}")
        
        elif not erro:
            try:
                df_new = pd.DataFrame([respostas])
                if os.path.exists(ARQUIVO_DB):
                    df_new.to_csv(ARQUIVO_DB, mode='a', header=False, index=False)
                else:
                    df_new.to_csv(ARQUIVO_DB, mode='w', header=True, index=False)
                
                st.balloons()
                st.success(f"✅ Transcrição do aluno {respostas['Nome']} salva com sucesso!")
                limpar_formulario()
                st.rerun()
            except PermissionError:
                st.error("❌ ERRO DE ARQUIVO: O Excel está aberto. Feche-o e tente de novo.")
            except Exception as e:
                st.error(f"❌ ERRO: {e}")

# --- AUTO-SAVE ---
try:
    with open(ARQUIVO_BACKUP, "w", encoding='utf-8') as f:
        json.dump(respostas, f, indent=4, ensure_ascii=False)
except: pass

# --- SEÇÃO 7: PAINEL ---
with tabs[6]:
    st.markdown("### 📊 STATUS DA DIGITALIZAÇÃO")
    if os.path.exists(ARQUIVO_DB):
        try:
            df = pd.read_csv(ARQUIVO_DB, dtype={'Matricula': str})
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Formulários Digitados", len(df))
            
            # Filtra colunas numéricas
            colunas_ignorar = ['Nome', 'Matricula', 'Semestre', 'Curriculo', 'Data_Registro', 'Petiano_Responsavel']
            cols_num = [c for c in df.columns if c not in colunas_ignorar and not c.startswith("Obs") and not c.startswith("Auto") and not c.startswith("Justificativa") and not c.startswith("Contribuição") and not c.startswith("Exemplos") and not c.startswith("Competências") and not c.startswith("Plano") and not c.startswith("Comentários")]
            
            df_n = df[cols_num].apply(pd.to_numeric, errors='coerce')
            if not df_n.empty:
                c2.metric("Média Geral (Notas)", f"{df_n.mean().mean():.2f}")
            
            if 'Data_Registro' in df.columns:
                last = pd.to_datetime(df['Data_Registro']).max()
                c3.metric("Último Registro", last.strftime("%d/%m %H:%M"))
            
            st.markdown("---")
            st.markdown("#### Conferência de Dados")
            st.dataframe(df, use_container_width=True, height=400)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Planilha de Dados (Backup)", csv, f"sac_backup_{datetime.now().strftime('%d%m%Y')}.csv", "text/csv")
        except Exception as e:
            st.error(f"Erro no banco: {e}")
    else:
        st.info("Nenhum formulário digitalizado ainda.")
