import os
import time
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
import requests

# ---------- Configuração de logs ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ---------- Carrega variáveis de ambiente ----------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")

MAX_CONTATOS = 3


def validar_variaveis_ambiente():
    """Garante que todas as variáveis necessárias estão configuradas."""
    faltando = []
    for nome, valor in [
        ("SUPABASE_URL", SUPABASE_URL),
        ("SUPABASE_KEY", SUPABASE_KEY),
        ("ZAPI_INSTANCE_ID", ZAPI_INSTANCE_ID),
        ("ZAPI_TOKEN", ZAPI_TOKEN),
        ("ZAPI_CLIENT_TOKEN", ZAPI_CLIENT_TOKEN),
    ]:
        if not valor:
            faltando.append(nome)

    if faltando:
        raise EnvironmentError(
            f"Variáveis de ambiente faltando no .env: {', '.join(faltando)}"
        )


def buscar_contatos(supabase: Client, limite: int = MAX_CONTATOS):
    """Busca contatos cadastrados no Supabase, limitado a `limite` registros."""
    try:
        response = (
            supabase.table("contatos")
            .select("nome_contato, telefone")
            .limit(limite)
            .execute()
        )
        contatos = response.data
        logger.info("Encontrados %d contato(s) no Supabase.", len(contatos))
        return contatos
    except Exception as e:
        logger.error("Erro ao buscar contatos no Supabase: %s", e)
        raise


def enviar_mensagem_zapi(telefone: str, mensagem: str):
    """Envia uma mensagem de texto via Z-API para o telefone informado."""
    url = (
        f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text"
    )
    payload = {"phone": telefone, "message": mensagem}

    headers = {"Client-Token": ZAPI_CLIENT_TOKEN}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        logger.info("Mensagem enviada com sucesso para %s.", telefone)
        return True
    except requests.exceptions.RequestException as e:
        detalhe = ""
        if e.response is not None:
            detalhe = e.response.text
        logger.error("Falha ao enviar mensagem para %s: %s | Detalhe: %s", telefone, e, detalhe)
        return False


def main():
    logger.info("Iniciando envio de mensagens...")

    validar_variaveis_ambiente()

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    contatos = buscar_contatos(supabase)

    if not contatos:
        logger.warning("Nenhum contato encontrado na tabela 'contatos'. Encerrando.")
        return

    sucesso = 0
    falha = 0

    for contato in contatos:
        nome = contato.get("nome_contato", "").strip()
        telefone = contato.get("telefone", "").strip()

        if not nome or not telefone:
            logger.warning("Contato com dados incompletos, pulando: %s", contato)
            falha += 1
            continue

        mensagem = f"Olá, {nome} tudo bem com você?"

        enviado = enviar_mensagem_zapi(telefone, mensagem)
        if enviado:
            sucesso += 1
        else:
            falha += 1

        time.sleep(2)  # pequeno intervalo entre envios

    logger.info("Processo finalizado. Sucesso: %d | Falha: %d", sucesso, falha)


if __name__ == "__main__":
    main()