# database.py
import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

@st.cache_resource
def iniciar_conexao():
    return st.connection("supabase", type=SupabaseConnection)

# O Cache dura 10 minutos ou até ser limpo manualmente
@st.cache_data(ttl=600)
def ler_banco_cacheados():
    conn = iniciar_conexao()
    try:
        response = conn.table("respostas_sac").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao ligar ao banco de dados: {e}")
        return pd.DataFrame()

def limpar_cache_banco():
    ler_banco_cacheados.clear()

def inserir_registro(dados_salvar):
    conn = iniciar_conexao()
    conn.table("respostas_sac").insert(dados_salvar).execute()
    limpar_cache_banco()

def atualizar_registro(sel_id, novos_dados):
    conn = iniciar_conexao()
    conn.table("respostas_sac").update(novos_dados).eq("Registro_ID", sel_id).execute()
    limpar_cache_banco()
