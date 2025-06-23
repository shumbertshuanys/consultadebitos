import pandas as pd
import os

def salvar_em_excel(lista_boletos, caminho_arquivo=r"C:\Users\user\Desktop\Automacao\resultado_marco.xlsx"):
    df = pd.DataFrame(lista_boletos)

    if os.path.exists(caminho_arquivo):
        df_existente = pd.read_excel(caminho_arquivo)
        df_total = pd.concat([df_existente, df], ignore_index=True)
    else:
        df_total = df

    df_total.to_excel(caminho_arquivo, index=False)

    abs_path = os.path.abspath(caminho_arquivo)
    print(f"Resultado salvo com sucesso em: {abs_path}")