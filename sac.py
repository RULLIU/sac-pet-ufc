import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="S.A.C. Completo", layout="wide")

st.title("S.A.C. - Sistema de Avaliação Curricular (DEQ/UFC)")
st.info("Preenchimento completo baseado no documento oficial.")

# Dicionário para armazenar respostas
respostas = {}

# [cite_start]--- 1. IDENTIFICAÇÃO [cite: 1-2] ---
st.header("1. Identificação")
c1, c2, c3 = st.columns(3)
respostas["nome"] = c1.text_input("Nome Completo")
respostas["matricula"] = c2.text_input("Matrícula")
respostas["semestre"] = c3.text_input("Semestre Atual")
respostas["curriculo"] = st.radio("Currículo:", ["2005.1", "2023.1"], horizontal=True)
respostas["data"] = st.date_input("Data", datetime.today())

st.markdown("---")

# --- FUNÇÃO GERADORA DE PERGUNTAS ---
def renderizar_pergunta(texto_pergunta, id_unica):
    """Gera o slider de 0-5 e o campo de comentário para cada questão"""
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.write(f"**{texto_pergunta}**")
        val = st.select_slider("", options=["0", "1", "2", "3", "4", "5"], value="0", key=f"nota_{id_unica}")
    with col_b:
        obs = st.text_input("Comentário (opcional)", key=f"obs_{id_unica}")
    
    # Salva no dicionário global
    respostas[f"{id_unica}_nota"] = val
    respostas[f"{id_unica}_obs"] = obs
    st.markdown("---")

# --- ORGANIZAÇÃO DAS ABAS ---
tabs = st.tabs([
    "Competências Fundamentais", 
    "Competências Gerais", 
    "Eng. Química Específica",
    "Disciplinas (Básicas)",
    "Disciplinas (Profissionais)",
    "Disciplinas (Avançadas)",
    "Reflexão Final"
])

# [cite_start]--- ABA 1: TÉCNICAS FUNDAMENTAIS [cite: 3-9] ---
with tabs[0]:
    st.subheader("1.1 Capacidades de Investigação e Análise")
    renderizar_pergunta("1. Projetar e conduzir experimentos e interpretar resultados", "q1")
    renderizar_pergunta("2. Desenvolver e/ou utilizar novas ferramentas e técnicas", "q2")
    
    st.subheader("1.2 Capacidades de Projeto e Concepção")
    renderizar_pergunta("3. Conceber, projetar e analisar sistemas, produtos e processos", "q3")

# [cite_start]--- ABA 2: COMPETÊNCIAS GERAIS [cite: 10-19] ---
with tabs[1]:
    st.subheader("2.1 Resolução de Problemas")
    renderizar_pergunta("4. Formular, conceber e avaliar soluções para problemas de engenharia", "q4")
    
    st.subheader("2.2 Análise e Compreensão Científica")
    renderizar_pergunta("5. Analisar e compreender fenômenos físicos e químicos através de modelos", "q5")
    
    st.subheader("2.3 Comunicação")
    renderizar_pergunta("6. Comunicar-se nas formas escrita, oral e gráfica", "q6")
    
    st.subheader("2.4 Trabalho em Equipe")
    renderizar_pergunta("7. Trabalhar e liderar equipes profissionais e multidisciplinares", "q7")
    
    st.subheader("2.5 Ética e Legislação")
    renderizar_pergunta("8. Aplicar ética e legislação no exercício profissional", "q8")

# [cite_start]--- ABA 3: ESPECÍFICAS EQ + PRÁTICA [cite: 20-40] ---
with tabs[2]:
    st.subheader("3. Competências Específicas")
    renderizar_pergunta("9. Aplicar conhecimentos matemáticos, científicos e tecnológicos", "q9")
    renderizar_pergunta("10. Compreender e modelar transferência de qtd de movimento, calor e massa", "q10")
    renderizar_pergunta("11. Aplicar conhecimentos de fenômenos de transporte ao projeto", "q11")
    renderizar_pergunta("12. Compreender mecanismos de transformação da matéria e energia", "q12")
    renderizar_pergunta("13. Projetar sistemas de recuperação, separação e purificação", "q13")
    renderizar_pergunta("14. Compreender mecanismos cinéticos de reações químicas", "q14")
    renderizar_pergunta("15. Projetar e otimizar sistemas reacionais e reatores", "q15")
    renderizar_pergunta("16. Projetar sistemas de controle de processos industriais", "q16")
    renderizar_pergunta("17. Projetar e otimizar plantas industriais (ambiental/segurança)", "q17")

    st.subheader("4. Eixos de Formação Prática")
    renderizar_pergunta("18. Aplicação de conhecimentos em projeto básico e dimensionamento", "q18")
    renderizar_pergunta("19. Execução de projetos de produção e melhorias de processos", "q19")

# [cite_start]--- ABA 4: DISCIPLINAS BÁSICAS [cite: 48-71] ---
with tabs[3]:
    st.info("Preencha apenas as disciplinas que cursou.")
    
    with st.expander("CÁLCULO DIFERENCIAL E INTEGRAL"):
        renderizar_pergunta("21. Analisar grandes volumes de dados", "calc_21")
        renderizar_pergunta("52. Formação Básica (cálculo, física, química, estatística)", "calc_52")

    with st.expander("FÍSICA GERAL"):
        renderizar_pergunta("22. Analisar criticamente a operação e manutenção de sistemas", "fis_22")
        renderizar_pergunta("53. Ciência da Engenharia (mecânica, resistência)", "fis_53")

    with st.expander("QUÍMICA GERAL E ANALÍTICA"):
        renderizar_pergunta("23. Aplicar conhecimentos de transformação a processos", "qui_23")
        renderizar_pergunta("24. Conceber e desenvolver produtos e processos", "qui_24")

    with st.expander("TERMODINÂMICA"):
        renderizar_pergunta("25. Projetar sistemas de suprimento energético", "termo_25")
        renderizar_pergunta("54. Ciência da Eng. Química (termodinâmica)", "termo_54")

    with st.expander("FENÔMENOS DE TRANSPORTE"):
        renderizar_pergunta("26. Aplicar conhecimentos de fenômenos de transporte", "ft_26")
        renderizar_pergunta("27. Comunicar-se tecnicamente e usar recursos gráficos", "ft_27")

    with st.expander("MECÂNICA DOS FLUIDOS"):
        renderizar_pergunta("28. Implantar, implementar e controlar soluções", "mecflu_28")
        renderizar_pergunta("29. Operar e supervisionar instalações", "mecflu_29")

# [cite_start]--- ABA 5: DISCIPLINAS PROFISSIONAIS [cite: 72-91] ---
with tabs[4]:
    with st.expander("OP. UNITÁRIAS I (Separações Mecânicas)"):
        renderizar_pergunta("30. Inspecionar e coordenar manutenção", "op1_30")
        renderizar_pergunta("55. Tecnologia Industrial (Op. Unit, Controle)", "op1_55")

    with st.expander("OP. UNITÁRIAS II (Transf. Massa)"):
        renderizar_pergunta("31. Elaborar estudos de impactos ambientais", "op2_31")
        renderizar_pergunta("32. Projetar processos de tratamento ambiental", "op2_32")

    with st.expander("REATORES QUÍMICOS"):
        renderizar_pergunta("33. Gerir recursos estratégicos na produção", "reat_33")
        renderizar_pergunta("34. Aplicar modelos de produção e qualidade", "reat_34")

    with st.expander("CONTROLE DE PROCESSOS"):
        renderizar_pergunta("35. Controle e supervisão de instalações", "ctrl_35")
        renderizar_pergunta("36. Gestão de empreendimentos industriais", "ctrl_36")

    with st.expander("PROJETO DE PLANTAS"):
        renderizar_pergunta("56. Projetos Industriais e Gestão", "proj_56")
        renderizar_pergunta("57. Ética, Meio Ambiente e Humanidades", "proj_57")

# [cite_start]--- ABA 6: DISCIPLINAS AVANÇADAS E COMPLEMENTARES [cite: 92-141] ---
with tabs[5]:
    st.write("Disciplinas Complementares, Avançadas e Integradoras")
    
    with st.expander("GESTÃO E ECONOMIA"):
        renderizar_pergunta("37. Eng. Econômica: Aprender novos conceitos", "econ_37")
        renderizar_pergunta("38. Eng. Econômica: Visão global", "econ_38")
        renderizar_pergunta("39. Gestão Produção: Comprometimento organizacional", "gest_39")
        renderizar_pergunta("40. Gestão Produção: Gerar resultados efetivos", "gest_40")

    with st.expander("AMBIENTAL E SEGURANÇA"):
        renderizar_pergunta("41. Eng. Ambiental: Inovação", "amb_41")
        renderizar_pergunta("42. Eng. Ambiental: Lidar com situações novas", "amb_42")
        renderizar_pergunta("43. Segurança: Lidar com incertezas", "seg_43")
        renderizar_pergunta("44. Segurança: Iniciativa e decisão", "seg_44")

    with st.expander("PRÁTICAS (Lab e Estágio)"):
        renderizar_pergunta("45. Laboratório: Criatividade", "lab_45")
        renderizar_pergunta("46. Laboratório: Relacionamento interpessoal", "lab_46")
        renderizar_pergunta("47. Estágio: Autocontrole emocional", "est_47")
        renderizar_pergunta("48. Estágio: Capacidade empreendedora", "est_48")

    with st.expander("OPTATIVAS (Biotec, Petróleo, Polímeros, Catálise)"):
        renderizar_pergunta("49. Biotec: Analisar grandes volumes de dados", "bio_49")
        renderizar_pergunta("50. Biotec: Novas ferramentas", "bio_50")
        renderizar_pergunta("51. Petróleo: Projetar sistemas de recuperação", "petro_51")
        renderizar_pergunta("52. Petróleo: Projetar reatores", "petro_52")
        renderizar_pergunta("53. Polímeros: Mecanismos cinéticos", "poli_53")
        renderizar_pergunta("54. Polímeros: Conceber produtos", "poli_54")
        renderizar_pergunta("55. Catálise: Mecanismos de transformação", "cat_55")
        renderizar_pergunta("56. Catálise: Aplicar conhecimentos a produção", "cat_56")

    with st.expander("INTEGRADORAS (Simulação, Otimização, TCC)"):
        renderizar_pergunta("57. Simulação: Analisar dados", "sim_57")
        renderizar_pergunta("58. Simulação: Comunicar-se tecnicamente", "sim_58")
        renderizar_pergunta("59. Otimização: Soluções para problemas", "otim_59")
        renderizar_pergunta("60. Otimização: Modelos de produção", "otim_60")
        renderizar_pergunta("61. TCC: Comunicação escrita/oral", "tcc_61")
        renderizar_pergunta("62. TCC: Liderar equipes", "tcc_62")

# [cite_start]--- ABA 7: REFLEXÃO FINAL [cite: 43-47] ---
with tabs[6]:
    st.header("Seção 6: Perguntas Reflexivas")
    
    # [cite_start]Competências Individuais [cite: 42]
    renderizar_pergunta("20. Capacidade de aprender rapidamente novos conceitos (Geral)", "q20_indiv")
    
    st.markdown("### Autoavaliação")
    respostas["auto_fortes"] = st.text_area("Quais competências considera como seus pontos fortes?")
    respostas["auto_fracos"] = st.text_area("Quais competências necessitam de maior desenvolvimento?")
    
    st.markdown("### Experiência Prática")
    respostas["exp_pratica"] = st.text_area("Como as atividades acadêmicas/profissionais contribuíram?")
    respostas["exemplos"] = st.text_area("Cite exemplos concretos onde aplicou competências:")
    
    st.markdown("### Futuro")
    respostas["futuro_essenciais"] = st.text_area("Quais competências considera essenciais para sua carreira?")
    respostas["futuro_plano"] = st.text_area("Como planeja continuar desenvolvendo suas competências?")
    
    st.markdown("---")
    respostas["obs_finais"] = st.text_area("Comentários Finais")

    # --- BOTÃO DE SALVAR ---
    st.markdown("---")
    if st.button("💾 SALVAR DADOS NO SISTEMA", type="primary"):
        if not respostas["nome"]:
            st.error("Erro: Preencha pelo menos o seu NOME na aba 'Identificação'.")
        else:
            # Cria DataFrame
            df = pd.DataFrame([respostas])
            
            # Nome do arquivo
            arquivo = "respostas_sac_deq.csv"
            
            # Verifica se arquivo existe para não apagar os dados anteriores
            if os.path.exists(arquivo):
                df.to_csv(arquivo, mode='a', header=False, index=False)
            else:
                df.to_csv(arquivo, mode='w', header=True, index=False)
            
            st.success(f"Sucesso! Dados salvos no arquivo: {arquivo}")
            st.info("Você pode fechar esta página ou preencher novamente para outro aluno.")