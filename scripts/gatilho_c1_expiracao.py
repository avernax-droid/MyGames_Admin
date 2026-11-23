# ==============================================================================
# PROJETO: MyGames - Backoffice
# MÓDULO: scripts/gatilho_c1_expiracao.py
# DATA DE CRIAÇÃO: Novembro/2026
# TÍTULO: Varredura de Expiração e Repescagem (Gatilhos C1 e C3)
# FUNÇÃO: Script autônomo (Cronjob) executado em duas etapas:
#         Etapa 1: Identifica protocolos em status_id = 1 que ultrapassaram
#                  PRAZO_POSTAGEM_HORAS, move-os para status_id = 19 (Prazo vencido -
#                  Em recuperação) e dispara o Gatilho C1 (protocolo_expirado).
#         Etapa 2: Identifica protocolos em repescagem (status_id 19, 20 ou 21)
#                  que atingiram o limite final (data reagendada vencida, carência
#                  de PRAZO_CARENCIA_EXPIRACAO_DIAS vencida ou timeout de recuperação),
#                  encerra-os definitivamente (status = 'Expirado', status_id = 18)
#                  e dispara o Gatilho C3 (protocolo_cancelado_prazo).
# HISTÓRICO DE ALTERAÇÕES:
# - 11/11/2026: Inclusão da política de retentativas (backoff 1m, 5m, 15m, 60m)
#               no disparar_gatilho_c1.
# - 16/11/2026: Padronização das variáveis .env (N8N_WEBHOOK_URL e
#               N8N_BEARER_TOKEN com sanitização), sincronização de
#               status = 'Expirado' com status_id = 18 e alinhamento do campo
#               motivo para 'prazo_de_postagem_expirado' conforme contrato N8N.
# - 21/11/2026: Implementação do fluxo de repescagem pós-expiração:
#               Etapa 1 move status_id 1 -> 19 e dispara C1 (protocolo_expirado);
#               Etapa 2 encerra definitivamente status_id 19/20/21 -> 18 ('Expirado')
#               e dispara o novo Gatilho C3 (protocolo_cancelado_prazo).
# - 23/11/2026: Ajuste na Etapa 2 para calcular a carência (status_id 21) e o
#               timeout de recuperação (status_id 19) a partir do vencimento do
#               prazo inicial de postagem (data_criacao + PRAZO_POSTAGEM_HORAS),
#               validando pela virada do dia civil (hoje_sp > data_limite.date()).
# ==============================================================================

import os
import re
import sys
import requests
import logging
import time
import mysql.connector
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
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
    format='%(asctime)s - [GATILHO_C1_C3] %(levelname)s - %(message)s'
)

# Credenciais Banco de Dados
DB_HOST = _limpar_env("DB_HOST")
DB_PORT = int(_limpar_env("DB_PORT", "3306"))
DB_USER = _limpar_env("DB_USER")
DB_PASS = _limpar_env("DB_PASS")
DB_NAME = _limpar_env("DB_NAME")

# Credenciais Webhook (Gatilhos C1 e C3 - Padrão Unificado) e Regras de Negócio
WEBHOOK_URL = _limpar_env("N8N_WEBHOOK_URL") or _limpar_env("WEBHOOK_AGENTE_URL_C1")
TOKEN_AGENTE = _limpar_env("N8N_BEARER_TOKEN") or _limpar_env("AGENTE_TOKEN_ENVIO")
AMBIENTE = _limpar_env("AMBIENTE_EXECUCAO", "homologacao").lower()
PRAZO_POSTAGEM_HORAS = int(_limpar_env("PRAZO_POSTAGEM_HORAS", "72"))
PRAZO_CARENCIA_EXPIRACAO_DIAS = int(_limpar_env("PRAZO_CARENCIA_EXPIRACAO_DIAS", "10"))


def conectar_bd():
    try:
        return mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME
        )
    except mysql.connector.Error as e:
        logging.error(f"Falha crítica na conexão com o banco de dados: {e}")
        sys.exit(1)


def _enviar_webhook_n8n(payload, rotulo_gatilho):
    """Envia payload JSON para o webhook N8N com política de retentativas (backoff)."""
    if not WEBHOOK_URL:
        logging.warning(f"N8N_WEBHOOK_URL não configurado. {rotulo_gatilho} não disparado.")
        return False

    numero_protocolo = payload.get("dados", {}).get("protocolo", "N/A")
    headers = {"Content-Type": "application/json"}
    if TOKEN_AGENTE:
        headers["Authorization"] = f"Bearer {TOKEN_AGENTE}"

    intervalos_retentativa = [60, 300, 900, 3600]
    tentativas = 0
    max_tentativas = len(intervalos_retentativa) + 1

    while tentativas < max_tentativas:
        try:
            logging.info(f"Disparando Webhook ({rotulo_gatilho}). Tentativa {tentativas + 1}/{max_tentativas}. Protocolo: {numero_protocolo}")
            resp = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=20)

            if resp.status_code == 200:
                try:
                    json_resp = resp.json()
                    if json_resp.get("ok") is True:
                        logging.info(f"Webhook ({rotulo_gatilho}) enviado e aceito com sucesso pelo N8N.")
                        return True
                    else:
                        logging.warning(f"Webhook ({rotulo_gatilho}) retornou HTTP 200 sem 'ok=true'. Retorno: {resp.text}")
                except ValueError:
                    logging.warning(f"Webhook ({rotulo_gatilho}) retornou HTTP 200, mas corpo não é JSON válido: {resp.text}")

            elif resp.status_code in (400, 401, 403, 404, 409):
                logging.error(f"Erro definitivo do cliente ou segurança (HTTP {resp.status_code}) em {rotulo_gatilho}. Retentativas abortadas. Retorno: {resp.text}")
                return False

            elif resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                espera_atual = int(retry_after) if retry_after else intervalos_retentativa[tentativas]
                logging.warning(f"Too Many Requests (HTTP 429) em {rotulo_gatilho}. Aguardando {espera_atual}s.")
                if tentativas < len(intervalos_retentativa):
                    time.sleep(espera_atual)
                    tentativas += 1
                    continue
                else:
                    return False

            else:
                logging.warning(f"Falha ao enviar Webhook ({rotulo_gatilho}). Status: {resp.status_code}. Retorno: {resp.text}")

        except requests.exceptions.Timeout:
            logging.error(f"Timeout ao enviar Webhook ({rotulo_gatilho}) na tentativa {tentativas + 1}.")
        except requests.exceptions.ConnectionError as ce:
            logging.error(f"Erro de conexão ao enviar Webhook ({rotulo_gatilho}) na tentativa {tentativas + 1}: {ce}")
        except Exception as e:
            logging.error(f"Erro inesperado ao enviar Webhook ({rotulo_gatilho}) na tentativa {tentativas + 1}: {e}")

        if tentativas < len(intervalos_retentativa):
            tempo_espera = intervalos_retentativa[tentativas]
            logging.info(f"Aguardando {tempo_espera}s para a próxima retentativa...")
            time.sleep(tempo_espera)

        tentativas += 1

    logging.error(f"Esgotadas as {max_tentativas} tentativas do Webhook ({rotulo_gatilho}) para o protocolo {numero_protocolo}. Evento pendente para reconciliação.")
    return False


def disparar_gatilho_c1(numero_protocolo, data_cancelamento):
    """Dispara Gatilho C1 (protocolo_expirado) para o N8N iniciar a régua de recuperação."""
    payload = {
        "evento": "protocolo_expirado",
        "dados": {
            "ambiente": AMBIENTE,
            "protocolo": numero_protocolo,
            "motivo": "prazo_de_postagem_expirado",
            "data_cancelamento": data_cancelamento
        }
    }
    return _enviar_webhook_n8n(payload, "Gatilho C1")


def disparar_gatilho_c3(numero_protocolo, motivo_c3, data_cancelamento):
    """Dispara Gatilho C3 (protocolo_cancelado_prazo) informando encerramento definitivo."""
    payload = {
        "evento": "protocolo_cancelado_prazo",
        "dados": {
            "ambiente": AMBIENTE,
            "protocolo": numero_protocolo,
            "motivo": motivo_c3,
            "data_cancelamento": data_cancelamento
        }
    }
    return _enviar_webhook_n8n(payload, "Gatilho C3")


def iniciar_recuperacao_local(protocolo_id, nota_laudo):
    """Move o protocolo de status_id = 1 para status_id = 19 (Prazo vencido - Em recuperação)."""
    db = conectar_bd()
    cursor = None
    try:
        cursor = db.cursor()

        query_update = """
            UPDATE protocolos_recompra 
            SET status_id = 19,
                laudo_tecnico = TRIM(CONCAT(IFNULL(laudo_tecnico, ''), '\n', %s))
            WHERE id = %s AND status = 'Aberto' AND status_id = 1
        """
        cursor.execute(query_update, (nota_laudo, protocolo_id))

        if cursor.rowcount == 0:
            db.rollback()
            return False

        query_log = """
            INSERT INTO historico_status_protocolo (protocolo_id, status_id, usuario_admin_id, data_alteracao)
            VALUES (%s, 19, 1, NOW())
        """
        cursor.execute(query_log, (protocolo_id,))

        db.commit()
        return True
    except mysql.connector.Error as e:
        logging.error(f"Erro ao mover protocolo ID {protocolo_id} para recuperação (status_id=19): {e}")
        db.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()


def encerrar_protocolo_definitivo_local(protocolo_id, nota_laudo):
    """Altera status macro para 'Expirado' e status_id para 18 ('Cancelado por prazo de postagem vencido')."""
    db = conectar_bd()
    cursor = None
    try:
        cursor = db.cursor()

        query_update = """
            UPDATE protocolos_recompra 
            SET status = 'Expirado', 
                status_id = 18,
                laudo_tecnico = TRIM(CONCAT(IFNULL(laudo_tecnico, ''), '\n', %s))
            WHERE id = %s AND status = 'Aberto' AND status_id IN (19, 20, 21)
        """
        cursor.execute(query_update, (nota_laudo, protocolo_id))

        if cursor.rowcount == 0:
            db.rollback()
            return False

        query_log = """
            INSERT INTO historico_status_protocolo (protocolo_id, status_id, usuario_admin_id, data_alteracao)
            VALUES (%s, 18, 1, NOW())
        """
        cursor.execute(query_log, (protocolo_id,))

        db.commit()
        return True
    except mysql.connector.Error as e:
        logging.error(f"Erro ao encerrar definitivamente protocolo ID {protocolo_id} (status_id=18): {e}")
        db.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()


def processar_etapa_1_recuperacao():
    """Etapa 1: Protocolos em status_id = 1 com mais de PRAZO_POSTAGEM_HORAS entram em recuperação (19) e disparam C1."""
    logging.info(f"[ETAPA 1] Verificando vencimentos iniciais (> {PRAZO_POSTAGEM_HORAS}h) para disparo do Gatilho C1...")
    db = conectar_bd()
    protocolos_vencidos = []
    cursor = None

    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT id, numero_protocolo, DATE_FORMAT(NOW(), '%d/%m/%Y') as data_hoje
            FROM protocolos_recompra 
            WHERE status = 'Aberto'
              AND status_id = 1 
              AND data_criacao < DATE_SUB(NOW(), INTERVAL %s HOUR)
        """
        cursor.execute(query, (PRAZO_POSTAGEM_HORAS,))
        protocolos_vencidos = cursor.fetchall()
    except Exception as e:
        logging.error(f"[ETAPA 1] Erro ao ler banco de dados: {e}")
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

    if not protocolos_vencidos:
        logging.info("[ETAPA 1] Nenhum protocolo vencido na janela inicial.")
        return

    logging.info(f"[ETAPA 1] Encontrados {len(protocolos_vencidos)} protocolos vencidos. Movendo para recuperação (status_id=19)...")
    nota_recuperacao = f"Prazo inicial de {PRAZO_POSTAGEM_HORAS}h vencido. Protocolo movido para recuperação (Gatilho C1 enviado ao N8N)."

    for p in protocolos_vencidos:
        prot_id = p['id']
        num_prot = p['numero_protocolo']
        data_hoje = p['data_hoje']

        if iniciar_recuperacao_local(prot_id, nota_recuperacao):
            logging.info(f"[ETAPA 1] Protocolo {num_prot} movido para status_id=19. Disparando C1...")
            disparar_gatilho_c1(num_prot, data_hoje)


def processar_etapa_2_encerramento_definitivo():
    """Etapa 2: Encerra definitivamente protocolos em status_id 19, 20 ou 21 cujo prazo final expirou e dispara C3."""
    logging.info(f"[ETAPA 2] Verificando protocolos em repescagem (19, 20, 21) para encerramento definitivo (Carência: {PRAZO_CARENCIA_EXPIRACAO_DIAS}d a partir do vencimento inicial)...")
    db = conectar_bd()
    candidatos = []
    cursor = None

    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                p.id,
                p.numero_protocolo,
                p.status_id,
                p.laudo_tecnico,
                p.data_criacao,
                DATE_FORMAT(NOW(), '%d/%m/%Y') as data_hoje,
                (
                    SELECT MAX(h.data_alteracao)
                    FROM historico_status_protocolo h
                    WHERE h.protocolo_id = p.id AND h.status_id = p.status_id
                ) as data_entrada_status
            FROM protocolos_recompra p
            WHERE p.status = 'Aberto'
              AND p.status_id IN (19, 20, 21)
        """
        cursor.execute(query)
        candidatos = cursor.fetchall()
    except Exception as e:
        logging.error(f"[ETAPA 2] Erro ao ler banco de dados: {e}")
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

    if not candidatos:
        logging.info("[ETAPA 2] Nenhum protocolo em repescagem encontrado.")
        return

    agora_local = datetime.now()
    agora_sp = datetime.now(ZoneInfo("America/Sao_Paulo"))
    hoje_sp = agora_sp.date()
    limite_carencia = agora_local - timedelta(days=PRAZO_CARENCIA_EXPIRACAO_DIAS)

    total_encerrados = 0

    for p in candidatos:
        prot_id = p['id']
        num_prot = p['numero_protocolo']
        status_atual = p['status_id']
        laudo = p.get('laudo_tecnico') or ''
        data_criacao = p.get('data_criacao')
        data_entrada = p.get('data_entrada_status') or data_criacao
        data_hoje_str = p['data_hoje']

        vencimento_inicial = data_criacao + timedelta(hours=PRAZO_POSTAGEM_HORAS) if data_criacao else None
        data_limite_carencia = vencimento_inicial + timedelta(days=PRAZO_CARENCIA_EXPIRACAO_DIAS) if vencimento_inicial else None

        deve_encerrar = False
        motivo_c3 = None
        nota_laudo = ""

        # Caso 1: Status 20 (Reagendado - Aguardando postagem)
        if status_atual == 20:
            matches = re.findall(r'\[REAGENDADO_ATE:\s*(\d{4}-\d{2}-\d{2})\]', laudo)
            if matches:
                try:
                    dt_reagendada = datetime.strptime(matches[-1], "%Y-%m-%d").date()
                    if hoje_sp > dt_reagendada:
                        deve_encerrar = True
                        motivo_c3 = "prazo_reagendamento_vencido"
                        nota_laudo = f"Encerramento definitivo (Gatilho C3): Data reagendada ({dt_reagendada.strftime('%d/%m/%Y')}) ultrapassada sem postagem."
                except ValueError:
                    logging.warning(f"[ETAPA 2] Tag de reagendamento mal formatada no protocolo {num_prot}.")
            elif data_entrada and data_entrada < limite_carencia:
                deve_encerrar = True
                motivo_c3 = "prazo_reagendamento_vencido"
                nota_laudo = "Encerramento definitivo (Gatilho C3): Prazo de reagendamento vencido sem postagem."

        # Caso 2: Status 21 (Aguardando postagem - Carência de 10 dias contados do vencimento inicial, até o fim do dia)
        elif status_atual == 21:
            if data_limite_carencia and hoje_sp > data_limite_carencia.date():
                deve_encerrar = True
                motivo_c3 = "prazo_carencia_vencido"
                nota_laudo = (
                    f"Encerramento definitivo (Gatilho C3): Período de carência de {PRAZO_CARENCIA_EXPIRACAO_DIAS} dias "
                    f"(limite até o fim de {data_limite_carencia.strftime('%d/%m/%Y')}, contado do vencimento inicial) encerrado sem postagem."
                )

        # Caso 3: Status 19 (Prazo vencido - Em recuperação - Timeout de segurança 10 dias do vencimento inicial, até o fim do dia)
        elif status_atual == 19:
            if data_limite_carencia and hoje_sp > data_limite_carencia.date():
                deve_encerrar = True
                motivo_c3 = "timeout_recuperacao"
                nota_laudo = (
                    f"Encerramento definitivo (Gatilho C3): Timeout de {PRAZO_CARENCIA_EXPIRACAO_DIAS} dias "
                    f"(limite até o fim de {data_limite_carencia.strftime('%d/%m/%Y')}, contado do vencimento inicial) em recuperação sem retorno do agente."
                )

        if deve_encerrar and motivo_c3:
            logging.info(f"[ETAPA 2] Encerrando definitivamente protocolo {num_prot} (Motivo: {motivo_c3})...")
            if encerrar_protocolo_definitivo_local(prot_id, nota_laudo):
                total_encerrados += 1
                disparar_gatilho_c3(num_prot, motivo_c3, data_hoje_str)

    logging.info(f"[ETAPA 2] Finalizada. Total de protocolos encerrados definitivamente: {total_encerrados}.")


def processar_varredura_expiracao():
    logging.info("Iniciando varredura diária de expiração e repescagem (Gatilhos C1 / C3)...")
    processar_etapa_1_recuperacao()
    processar_etapa_2_encerramento_definitivo()
    logging.info("Varredura de expiração e repescagem (Gatilhos C1 / C3) finalizada com sucesso.")


if __name__ == "__main__":
    processar_varredura_expiracao()
