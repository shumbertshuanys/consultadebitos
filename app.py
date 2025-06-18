import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from bot_superlogica import consultar_superlogica

# Conectar ao banco de dados SQLite
conn = sqlite3.connect("cadastro_imoveis.db", check_same_thread=False)
c = conn.cursor()

# Criar tabela se não existir
c.execute('''
    CREATE TABLE IF NOT EXISTS administradoras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        plataforma TEXT,
        url TEXT,
        login TEXT,
        senha TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS resultados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        administradora_id INTEGER,
        condominio_nome TEXT,
        unidade TEXT,
        status TEXT,
        valor TEXT,
        vencimento TEXT,
        resultado_raw TEXT
    )
''')
conn.commit()

st.title("🔎 Consulta Condominial - Painel de Administradoras")

# Cadastro de administradora
with st.form("Cadastro"):
    nome = st.text_input("Nome da Administradora")
    plataforma = st.selectbox("Plataforma", ["Superlogica", "COM21", "Condomob", "Classecon", "Outros"])
    url = st.text_input("URL de Acesso")
    login = st.text_input("Login")
    senha = st.text_input("Senha", type="password")
    submitted = st.form_submit_button("Cadastrar")
    if submitted:
        c.execute('''
            INSERT INTO administradoras (nome, plataforma, url, login, senha)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, plataforma, url, login, senha))
        conn.commit()
        st.success("✅ Administradora cadastrada com sucesso!")

# Visualização
st.subheader("🏢 Administradoras Cadastradas")
adm_df = pd.read_sql_query("SELECT * FROM administradoras", conn)
st.dataframe(adm_df)

# Botão de consulta
st.subheader("🔍 Consultar Débitos nas Plataformas")
if st.button("Consultar todos - Superlogica"):
    superlogica_df = adm_df[adm_df["plataforma"] == "Superlogica"]
    for _, row in superlogica_df.iterrows():
        st.write(f"Consultando: {row['nome']}...")

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        # Maximizar a janela do navegador
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")

        resultados = consultar_superlogica(row["url"], row["login"], row["senha"], row["nome"], chrome_options)

        for r in resultados:
            c.execute("""
                INSERT INTO resultados (administradora_id, condominio_nome, unidade, status, valor, vencimento, resultado_raw)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row["id"],
                r.get("condominio_nome", "-"),
                r.get("unidade", "-"),
                r.get("status", "-"),
                r.get("valor", "-"),
                r.get("vencimento", "-"),
                str(r)
            ))
        conn.commit()
    st.success("Consulta concluída!")

# Resultados
st.subheader("📄 Resultados das Consultas")
df_resultados = pd.read_sql_query("SELECT * FROM resultados ORDER BY id DESC", conn)

# Conversão de datas
df_resultados["vencimento_data"] = pd.to_datetime(df_resultados["vencimento"].str.extract(r'(\d{2}/\d{2}/\d{4})')[0], format="%d/%m/%Y", errors="coerce")
hoje = datetime.now().date()

vencidos = df_resultados[df_resultados["vencimento_data"].dt.date < hoje]
em_aberto = df_resultados[df_resultados["status"] == "Em aberto"]
sem_boletos = df_resultados[df_resultados["status"] == "Sem boletos em aberto"]
erros = df_resultados[df_resultados["status"].str.contains("Erro")]

st.subheader("📊 Dashboard Detalhado")

with st.expander("📬 Boletos em aberto"):
    st.metric("Quantidade", len(em_aberto))
    cols = [col for col in ["administradora_id", "condominio_nome", "unidade", "valor", "vencimento"] if col in em_aberto.columns]
    if cols:
        st.dataframe(em_aberto[cols].sort_values(by=cols[-1]))
    else:
        st.warning("⚠️ As colunas esperadas não foram encontradas.")

with st.expander("🔴 Boletos vencidos"):
    st.metric("Quantidade", len(vencidos))
    cols = [col for col in ["administradora_id", "condominio_nome", "unidade", "valor", "vencimento"] if col in vencidos.columns]
    if cols:
        if "vencimento_data" in vencidos.columns:
            st.dataframe(vencidos[cols + ["vencimento_data"]].sort_values(by="vencimento_data"))
        else:
            st.dataframe(vencidos[cols])
    else:
        st.warning("⚠️ As colunas esperadas não foram encontradas.")

with st.expander("✅ Sem boletos em aberto"):
    st.metric("Quantidade", len(sem_boletos))
    cols = [col for col in ["administradora_id", "condominio_nome", "unidade"] if col in sem_boletos.columns]
    if cols:
        st.dataframe(sem_boletos[cols].sort_values(by="condominio_nome"))
    else:
        st.warning("⚠️ As colunas esperadas não foram encontradas.")

with st.expander("❗ Ocorrências de erro"):
    st.metric("Quantidade", len(erros))
    cols = [col for col in ["administradora_id", "condominio_nome", "unidade", "status"] if col in erros.columns]
    if cols:
        st.dataframe(erros[cols])
    else:
        st.warning("⚠️ As colunas esperadas não foram encontradas.")

st.subheader("📈 Totais Gerais")
st.metric("🏢 Total de condomínios analisados", df_resultados['condominio_nome'].nunique())
st.metric("📦 Total de unidades analisadas", df_resultados['unidade'].nunique())
