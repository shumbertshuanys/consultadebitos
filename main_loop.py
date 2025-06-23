from consulta_marco import consulta_marco
from utils import salvar_em_excel
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Leitura da planilha
df = pd.read_excel("acessos_administradoras_FINAL.xlsx")
df = df[df["Administradora"].str.lower() == "marco condominial"]
print(f"Total de unidades Marco Condominial encontradas: {len(df)}")

resultados = []

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    for idx, linha in df.iterrows():
        unidade_dict = linha.to_dict()
        print(f"\n🔍 Consultando unidade {unidade_dict['Unidade']} do condomínio {unidade_dict['Condominio']}...")

        try:
            primeira_vez = len(resultados) == 0
            boletos = consulta_marco(driver, unidade_dict, primeira_vez=primeira_vez)
            resultados.extend(boletos)
        except Exception as e:
            print(f"⚠️ Erro ao consultar {unidade_dict['Condominio']} - {unidade_dict['Unidade']}: {e}")

    salvar_em_excel(resultados)
except Exception as e:
    print("❌ Erro geral:", e)
finally:
    driver.quit()
