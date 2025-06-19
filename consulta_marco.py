from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import re

def consulta_marco(driver, unidade_dict):
    """
    Consulta débitos da plataforma Marco Condominial.
    """
    url = unidade_dict['Site de Acesso']
    login = unidade_dict['Login']
    senha = unidade_dict['Senha']
    condominio = unidade_dict['Condominio']
    unidade = unidade_dict['Unidade']  # Ex: "0101", "204", etc.

    boletos = []

    driver.get(url)
    time.sleep(3)

    # Login
    driver.find_element(By.XPATH, '//*[@id="email"]').send_keys(login)
    driver.find_element(By.XPATH, '//*[@id="salvar"]').click()
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="senha"]').send_keys(senha)
    driver.find_element(By.XPATH, '//*[@id="salvar"]').click()
    print("Login realizado com sucesso.")
    time.sleep(4)

    # Abrir dropdown lateral
    try:
        driver.find_element(By.XPATH, '//*[@id="menu-principal acesso-morador"]/li[3]/div/img').click()
        print("Dropdown do condomínio clicado.")
        time.sleep(1)
    except Exception as e:
        print(f"Erro ao abrir dropdown: {e}")
        return []

    # Buscar e selecionar condomínio
    campo_filtro = driver.find_element(By.XPATH, '//*[@id="filtro"]')
    campo_filtro.send_keys(condominio)
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="lista"]').click()
    print("Condomínio selecionado.")
    print("Aguardando boletos ou mensagem 'não há boletos'...")
    time.sleep(3)
    print(driver.page_source)  # <- Esse vai mostrar o HTML completo no terminal

# Espera a div dos boletos ou mensagem de ausência
try:
    WebDriverWait(driver, 15).until(
        EC.any_of(
            EC.presence_of_element_located((By.XPATH, '//*[contains(@id, "div_nenhuma_cobranca")]/div/b')),
            EC.presence_of_element_located((By.XPATH, '//*[starts-with(@id, "grid_cobranca_")]/div[2]'))
        )
    )
except:
    print("Nenhum resultado encontrado.")
    return []

# Verifica ausência de boletos
try:
    mensagem = driver.find_element(By.XPATH, '//*[contains(@id, "div_nenhuma_cobranca")]/div/b')
    if "não há boletos" in mensagem.text.lower():
        boletos.append({
            "Condominio": condominio,
            "Unidade": unidade,
            "Vencimento": None,
            "Valor": 0.0,
            "Status": "Sem débitos"
        })
        return boletos
except:
    pass

# Captura lista de boletos
try:
    container = driver.find_element(By.XPATH, '//*[starts-with(@id, "grid_cobranca_")]/div[2]')
    blocos = container.find_elements(By.CLASS_NAME, 'linha-cobranca')

    for bloco in blocos:
        try:
            unidade_bloco = bloco.find_element(By.CLASS_NAME, 'unidade').text
            if unidade in unidade_bloco:
                vencimento_raw = bloco.find_element(By.CLASS_NAME, 'vencimento').text
                valor_raw = bloco.find_element(By.CLASS_NAME, 'valor').text

                vencimento = re.findall(r'\d{2}/\d{2}/\d{4}', vencimento_raw)[0]
                valor = float(valor_raw.replace("R$", "").replace(".", "").replace(",", ".").strip())

                boletos.append({
                    "Condominio": condominio,
                    "Unidade": unidade,
                    "Vencimento": vencimento,
                    "Valor": valor,
                    "Status": "Em aberto"
                })
        except Exception as e:
            print(f"Erro ao processar um bloco: {e}")
except Exception as e:
    print(f"Erro ao coletar boletos: {e}")

return boletos
