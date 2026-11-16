# ==============================================================================
# PROJETO: MyGames - Backoffice
# MÓDULO: scripts/gatilho_c1_expiracao.py
# DATA DE CRIAÇÃO: Novembro/2026
# TÍTULO: Varredura de Expiração (Gatilho C1)
# FUNÇÃO: Script autônomo (Cronjob) para verificar protocolos que ultrapassaram
#         o prazo limite estipulado (PRAZO_POSTAGEM_HORAS). Altera o status
#         macro para 'Expirado' e status_id para 18 ('Cancelado por prazo de
#         postagem vencido') e dispara o Webhook para o Agente N8N.
# HISTÓRICO DE ALTERAÇÕES:
# - 11/11/2026: Inclusão da política de retentativas (backoff 1m, 5m, 15m, 60m)
#               no disparar_gatilho_c1.
# - 16/11/2026: Padronização das variáveis .env (N8N_WEBHOOK_URL e
#               N8N_BEARER_TOKEN com sanitização), sincronização de
#               status = 'Expirado' com status_id = 18 e alinhamento do campo
#               motivo para 'prazo_de_postagem_expirado' conforme contrato N8N.
# ==============================================================================

import os
import sys
import requests
import logging
import time
import mysql.connector
from dotenv import load_dotenv

# Define caminhos e carrega .env do Admin
caminho_env_admin = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
load_dotenv(dotenv_path=caminho_env_admin)


def _limpar_env(chave, padrao=""):
    valor = os.getenv(chave, padrao)
    return valor.strip().strip('"').strip("'") if valor else padrao


# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [GATILHO_C1] %(levelname)s - %(message)s'
)

# Credenciais Banco de Dados
DB_HOST = _limpar_env("DB_HOST")
DB_PORT = int(_limpar_env("DB_PORT", "3306"))
DB_USER = _limpar_env("DB_USER")
DB_PASS = _limpar_env("DB_PASS")
DB_NAME = _limpar_env("DB_NAME")

# Credenciais Webhook (Gatilho C1) e Regras de Negócio
WEBHOOK_URL = _limpar_env("N8N_WEBHOOK_URL") or _limpar_env("WEBHOOK_AGENTE_URL_C1")
TOKEN_AGENTE = _limpar_env("N8N_BEARER_TOKEN") or _limpar_env("AGENTE_TOKEN_ENVIO")
AMBIENTE = _limpar_env("AMBIENTE_EXECUCAO", "homologacao")
PRAZO_POSTAGEM_HORAS = int(_limpar_env("PRAZO_POSTAGEM_HORAS", "72"))


def conectar_bd():
    try:
        return mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME
        )
    except mysql.connector.Error as e:
        logging.error(f"Falha crítica na conexão com o banco de dados: {e}")
        sys.exit(1)


def disparar_gatilho_c1(numero_protocolo, data_cancelamento):
    """Envia o POST para a API do Agente de WhatsApp informando o cancelamento automático, com retentativas."""
    if not WEBHOOK_URL:
        logging.warning("N8N_WEBHOOK_URL / WEBHOOK_AGENTE_URL_C1 não configurado. Gatilho C1 não disparado.")
        return False

    payload = {
        "evento": "protocolo_expirado",
        "dados": {
            "ambiente": AMBIENTE,
            "protocolo": numero_protocolo,
            "motivo": "prazo_de_postagem_expirado",
            "data_cancelamento": data_cancelamento
        }
    }

    headers = {"Content-Type": "application/json"}
    if TOKEN_AGENTE:
        headers["Authorization"] = f"Bearer {TOKEN_AGENTE}"

    intervalos_retentativa = [60, 300, 900, 3600]
    tentativas = 0
    max_tentativas = len(intervalos_retentativa) + 1

    while tentativas < max_tentativas:
        try:
            logging.info(f"Disparando Webhook (Gatilho C1). Tentativa {tentativas + 1}/{max_tentativas}. Protocolo: {numero_protocolo}")
            resp = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=20)

            if resp.status_code == 200:
                try:
                    json_resp = resp.json()
                    if json_resp.get("ok") is True:
                        logging.info("Webhook (Gatilho C1) enviado e aceito com sucesso pelo N8N.")
                        return True
                    else:
                        logging.warning(f"Webhook (Gatilho C1) retornou HTTP 200 sem 'ok=true'. Retorno: {resp.text}")
                except ValueError:
                    logging.warning(f"Webhook (Gatilho C1) retornou HTTP 200, mas corpo não é JSON válido: {resp.text}")

            elif resp.status_code in (400, 401, 403, 404, 409):
                logging.error(f"Erro definitivo do cliente ou segurança (HTTP {resp.status_code}). Retentativas abortadas. Retorno: {resp.text}")
                return False

            elif resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                espera_atual = int(retry_after) if retry_after else intervalos_retentativa[tentativas]
                logging.warning(f"Too Many Requests (HTTP 429). Aguardando {espera_atual}s.")
                if tentativas < len(intervalos_retentativa):
                    time.sleep(espera_atual)
                    tentativas += 1
                    continue
                else:
                    return False

            else:
                logging.warning(f"Falha ao enviar Webhook (Gatilho C1). Status: {resp.status_code}. Retorno: {resp.text}")

        except requests.exceptions.Timeout:
            logging.error(f"Timeout ao enviar Webhook (Gatilho C1) na tentativa {tentativas + 1}.")
        except requests.exceptions.ConnectionError as ce:
            logging.error(f"Erro de conexão ao enviar Webhook (Gatilho C1) na tentativa {tentativas + 1}: {ce}")
        except Exception as e:
            logging.error(f"Erro inesperado ao enviar Webhook (Gatilho C1) na tentativa {tentativas + 1}: {e}")

        if tentativas < len(intervalos_retentativa):
            tempo_espera = intervalos_retentativa[tentativas]
            logging.info(f"Aguardando {tempo_espera}s para a próxima retentativa...")
            time.sleep(tempo_espera)

        tentativas += 1

    logging.error(f"Esgotadas as {max_tentativas} tentativas do Webhook (Gatilho C1) para o protocolo {numero_protocolo}. Evento pendente para reconciliação.")
    return False


def cancelar_protocolo_local(protocolo_id, motivo):
    """Altera o status macro para 'Expirado' e status_id para 18 ('Cancelado por prazo de postagem vencido') e registra no histórico."""
    db = conectar_bd()
    cursor = None
    try:
        cursor = db.cursor()

        # Sincroniza status macro ('Expirado') e esteira operacional (status_id = 18)
        query_update = "UPDATE protocolos_recompra SET status = 'Expirado', status_id = 18 WHERE id = %s"
        cursor.execute(query_update, (protocolo_id,))

        # ID 1 para o admin fictício 'Sistema' no histórico
        query_log = """
            INSERT INTO historico_status_protocolo (protocolo_id, status_id, usuario_admin_id, data_alteracao)
            VALUES (%s, 18, 1, NOW())
        """
        cursor.execute(query_log, (protocolo_id,))

        # Adiciona o motivo ao laudo_tecnico
        query_laudo = "UPDATE protocolos_recompra SET laudo_tecnico = CONCAT(IFNULL(laudo_tecnico, ''), '\n\n', %s) WHERE id = %s"
        cursor.execute(query_laudo, (motivo, protocolo_id))

        db.commit()
        return True
    except mysql.connector.Error as e:
        logging.error(f"Erro ao atualizar status DB (Protocolo ID {protocolo_id}): {e}")
        db.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()


def processar_varredura_expiracao():
    logging.info(f"Iniciando varredura diária de expiração (Gatilho C1) - Prazo: {PRAZO_POSTAGEM_HORAS}h...")
    db = conectar_bd()
    protocolos_expirados = []
    cursor = None

    try:
        cursor = db.cursor(dictionary=True)
        # Seleciona Status 1 (Aguardando cliente) que ultrapassaram o prazo
        query = """
            SELECT id, numero_protocolo, DATE_FORMAT(NOW(), '%d/%m/%Y') as data_hoje
            FROM protocolos_recompra 
            WHERE status_id = 1 
              AND data_criacao < DATE_SUB(NOW(), INTERVAL %s HOUR)
        """
        cursor.execute(query, (PRAZO_POSTAGEM_HORAS,))
        protocolos_expirados = cursor.fetchall()

    except Exception as e:
        logging.error(f"Erro ao ler banco de dados: {e}")
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

    if not protocolos_expirados:
        logging.info("Nenhum protocolo expirado encontrado na varredura.")
        return

    logging.info(f"Encontrados {len(protocolos_expirados)} protocolos expirados. A processar cancelamentos...")

    motivo_cancelamento = "Cancelamento automático pelo sistema (Gatilho C1): Prazo de envio expirado."

    for p in protocolos_expirados:
        prot_id = p['id']
        num_prot = p['numero_protocolo']
        data_hoje = p['data_hoje']

        logging.info(f"A cancelar protocolo {num_prot}...")

        # 1. Atualiza Banco de Dados
        if cancelar_protocolo_local(prot_id, motivo_cancelamento):
            # 2. Dispara o Gatilho
            disparar_gatilho_c1(num_prot, data_hoje)

    logging.info("Varredura de expiração (Gatilho C1) finalizada com sucesso.")


if __name__ == "__main__":
    processar_varredura_expiracao()