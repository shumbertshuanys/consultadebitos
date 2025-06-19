from selenium import webdriver
from consulta_marco import consulta_marco
import pandas as pd

# Lê a planilha de acesso
df = pd.read_excel("acessos_administradoras_FINAL.xlsx")

# Filtra apenas administradora Marco - aqui estamos testando só a 1ª linha
linha = df.iloc[0].to_dict()

# Inicia o driver do Chrome
driver = webdriver.Chrome()

# Executa a consulta de boletos
resultado = consulta_marco(driver, linha)

# Encerra o navegador
driver.quit()

# Exibe os resultados coletados
for r in resultado:
    print(r)
