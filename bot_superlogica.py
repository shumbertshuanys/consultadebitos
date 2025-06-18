import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def consultar_superlogica(url, login, senha, administradora_nome, chrome_options):
    resultados = []

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "usuario"))).send_keys(login)
        driver.find_element(By.ID, "senha").send_keys(senha)
        driver.find_element(By.ID, "entrar").click()

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "menu-condominios")))
        menu_condominios = driver.find_element(By.ID, "menu-condominios")

        ActionChains(driver).move_to_element(menu_condominios).perform()
        time.sleep(2)

        condominios = driver.find_elements(By.CSS_SELECTOR, "ul.listagem > li > a")
        cond_data = [(el.get_attribute("id"), el.text.strip()) for el in condominios if el.get_attribute("id") and el.text.strip()]

        print(f"🔍 {len(cond_data)} encontrados: {cond_data}")

        for cond_id, cond_nome in cond_data:
            try:
                try:
                    ActionChains(driver).move_to_element(menu_condominios).perform()
                    time.sleep(0.5)
                    driver.find_element(By.ID, cond_id).click()
                except:
                    driver.execute_script(f"document.getElementById('{cond_id}').click()")

                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "conteudo-principal")))
                time.sleep(3)

                if driver.find_elements(By.CLASS_NAME, "div-nenhuma-cobranca"):
                    resultados.append({
                        "administradora": administradora_nome,
                        "condominio_id": cond_id,
                        "condominio_nome": cond_nome,
                        "status": "Sem boletos em aberto",
                        "valor": "-",
                        "vencimento": "-",
                        "mensagem": "Não há boletos",
                        "unidade": "-",
                        "vencimento_data": ""
                    })
                    continue

                boletos = driver.find_elements(By.CSS_SELECTOR, "a.bloco-grid-cobrancas")

                for boleto in boletos:
                    try:
                        unidade = boleto.find_element(By.CSS_SELECTOR, "div.unidade div.numero").text.strip()
                        valor = boleto.find_element(By.CSS_SELECTOR, "div.valor").text.strip()
                        vencimento = boleto.find_element(By.CSS_SELECTOR, "div.vencimento").text.strip()

                        venc_data_match = re.search(r"(\d{2}/\d{2}/\d{4})", vencimento)
                        venc_data = datetime.strptime(venc_data_match.group(1), "%d/%m/%Y") if venc_data_match else None

                        status = "Vencido" if venc_data and venc_data < datetime.now() else "Em aberto"

                        resultados.append({
                            "administradora": administradora_nome,
                            "condominio_id": cond_id,
                            "condominio_nome": cond_nome,
                            "status": status,
                            "valor": valor,
                            "vencimento": vencimento,
                            "mensagem": f"Boleto da unidade {unidade}",
                            "unidade": unidade,
                            "vencimento_data": venc_data.strftime("%Y-%m-%d") if venc_data else ""
                        })

                    except Exception as e:
                        print(f"Erro ao extrair boleto: {e}")
                        continue

            except Exception as e:
                print(f"Erro ao processar condomínio {cond_id} - {cond_nome}: {e}")
                resultados.append({
                    "administradora": administradora_nome,
                    "condominio_id": cond_id,
                    "condominio_nome": cond_nome,
                    "status": "Erro ao verificar boletos",
                    "valor": "-",
                    "vencimento": "-",
                    "mensagem": "Erro ao acessar boletos",
                    "unidade": "-",
                    "vencimento_data": ""
                })

    finally:
        print("✅ Finalizando sessão do navegador...")
        driver.quit()

    return resultados
