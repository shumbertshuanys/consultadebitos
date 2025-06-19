from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def consulta_marco(driver, unidade_dict, primeira_vez=False):
    print(f"Driver conectado: {driver}")

    url = unidade_dict["Site de Acesso"]
    usuario = unidade_dict["Login"]
    senha = str(unidade_dict["Senha"])
    condominio = unidade_dict["Condominio"]
    unidade = str(unidade_dict["Unidade"]).strip()

    boletos = []

# Remove espaços, hífens e pontos, separando número de letra (ex: "1 B" -> "0001 B")
unidade_tratada = (
    unidade.lower().replace(" ", "").replace("-", "").replace(".", "")
)

# Extrai número e letra separadamente
import re
match = re.match(r"(\d+)([a-z]*)", unidade_tratada)
if match:
    numero = match.group(1).zfill(4)[-4:]  # Preenche com zero à esquerda até 4 dígitos
    letra = match.group(2)
    unidade_formatada = numero + letra
else:
    unidade_formatada = unidade_tratada  # fallback se regex falhar

    print(f"Unidade formatada: {unidade_formatada}")

    if primeira_vez:
        print(f"Acessando URL: {url}")
        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "email"))
        ).send_keys(usuario)

        driver.find_element(By.NAME, "senha").send_keys(senha)
        driver.find_element(By.ID, "login-btn").click()
        print("Login realizado com sucesso.")
        time.sleep(2)

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(@class,"button-open-menu")]'))
        ).click()
        print("Dropdown do condomínio clicado.")
    except:
        print("⚠️ Falha ao abrir o menu lateral.")
        return []

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//div[contains(text(),"{condominio}")]'))
        ).click()
        print("Condomínio selecionado.")
    except:
        print("⚠️ Falha ao selecionar o condomínio.")
        return []

    print("Aguardando boletos ou mensagem 'não há boletos'...")
    time.sleep(5)
    print("⌛ Verificando se há boletos ou mensagem de ausência de boletos...")

    try:
        unit_container = driver.find_element(By.XPATH, '//div[contains(@id,"grid_cobranca")]/div[2]')
        print("✅ Container de unidades com boletos identificado.")
        unidades_com_boletos = unit_container.find_elements(By.CLASS_NAME, "unidade")

        for unidade_elemento in unidades_com_boletos:
            print("🔎 Verificando unidade:", unidade_elemento.text)
            try:
                unidade_nome = unidade_elemento.find_element(By.CLASS_NAME, "nome-unidade").text.strip().lower().replace(" ", "")
                unidade_nome_formatada = unidade_nome.zfill(5)
                print(f"Comparando unidade atual '{unidade_nome_formatada}' com alvo '{unidade_formatada}'")

                if unidade_nome_formatada != unidade_formatada:
                    print(f"❌ Unidade ignorada: {unidade_nome_formatada}, buscando por: {unidade_formatada}")
                    continue

                vencimentos = unidade_elemento.find_elements(By.CLASS_NAME, "vencimento")
                valores = unidade_elemento.find_elements(By.CLASS_NAME, "valor")
                for venc, val in zip(vencimentos, valores):
                    vencimento = venc.text.strip()
                    valor = val.text.strip()
                    boletos.append({
                        "Condominio": condominio,
                        "Unidade": unidade,
                        "Vencimento": vencimento,
                        "Valor": valor,
                        "Status": "Débito em aberto"
                    })
                    print(f"✅ Débito identificado - Vencimento: {vencimento}, Valor: {valor}")
            except Exception as e:
                print(f"Erro ao processar unidade: {e}")

        if len(boletos) == 0:
            print("⚠️ Nenhuma unidade correspondente localizada — salvando HTML para análise.")
            with open("html_debug_unidade.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

    except:
        try:
            sem_boletos = driver.find_element(By.XPATH, '//*[contains(text(),"não há boletos")]')
            if sem_boletos:
                print("ℹ️ Nenhum boleto encontrado para a unidade.")
                boletos.append({
                    "Condominio": condominio,
                    "Unidade": unidade,
                    "Vencimento": None,
                    "Valor": 0.0,
                    "Status": "Sem débitos"
                })
        except:
            print("⚠️ Não foi possível localizar boletos nem mensagem padrão de ausência.")

    return boletos
