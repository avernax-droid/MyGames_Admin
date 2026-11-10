# ==============================================================================
# PROJETO: MyGames - Backoffice
# MÓDULO: scripts/gatilho_c1_expiracao.py
# DATA DE CRIAÇÃO: Novembro/2026
# TÍTULO: Varredura de Expiração (Gatilho C1)
# FUNÇÃO: Script autónomo (Cronjob) para verificar protocolos que ultrapassaram
# o prazo limite estipulado (PRAZO_POSTAGEM_HORAS). Altera o status para 
# 'Cancelado Limite Postagem' (ID 18) e dispara o Webhook para o Agente N8N.
# ==============================================================================

import os
import sys
import requests
import logging
import mysql.connector
from dotenv import load_dotenv

# Define caminhos e carrega .env do Admin
caminho_env_admin = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
load_dotenv(dotenv_path=caminho_env_admin)

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [GATILHO_C1] %(levelname)s - %(message)s'
)

# Credenciais Banco de Dados
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# Credenciais Webhook (Gatilho C1) e Regras de Negócio
WEBHOOK_URL = os.getenv('WEBHOOK_AGENTE_URL_C1')
TOKEN_AGENTE = os.getenv('AGENTE_TOKEN_ENVIO')
AMBIENTE = os.getenv('AMBIENTE_EXECUCAO', 'homologacao')
PRAZO_POSTAGEM_HORAS = int(os.getenv('PRAZO_POSTAGEM_HORAS', 72))

def conectar_bd():
    try:
        return mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME
        )
    except mysql.connector.Error as e:
        logging.error(f"Falha crítica na conexão com o banco de dados: {e}")
        sys.exit(1)

def disparar_gatilho_c1(numero_protocolo, data_cancelamento):
    """Envia o POST para a API do Agente de WhatsApp informando o cancelamento automático."""
    if not WEBHOOK_URL:
        logging.warning("WEBHOOK_AGENTE_URL_C1 não configurado. Gatilho C1 não disparado.")
        return False
        
    payload = {
        "evento": "protocolo_expirado",
        "dados": {
            "protocolo": numero_protocolo,
            "motivo": "Prazo excedido na virada do dia limite",
            "data_cancelamento": data_cancelamento,
            "ambiente": AMBIENTE
        }
    }
    
    headers = {"Content-Type": "application/json"}
    if TOKEN_AGENTE:
        headers["Authorization"] = f"Bearer {TOKEN_AGENTE}"
        
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        if resp.status_code in [200, 201]:
            logging.info(f"Gatilho C1 disparado com sucesso para {numero_protocolo}.")
            return True
        else:
            logging.error(f"Falha no Webhook (Gatilho C1). Status: {resp.status_code} | Resposta: {resp.text}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Timeout/Erro ao conectar no Webhook do Agente: {e}")
        return False

def cancelar_protocolo_local(protocolo_id, motivo):
    """Altera o status do protocolo para 18 (Cancelado limite postagem) e regista no histórico."""
    db = conectar_bd()
    try:
        cursor = db.cursor()
        
        # Atualiza o status para 18 (Cancelado limite de tempo postagem)
        query_update = "UPDATE protocolos_recompra SET status_id = 18 WHERE id = %s"
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
        if db and db.is_connected():
            cursor.close()
            db.close()

def processar_varredura_expiracao():
    logging.info(f"Iniciando varredura diária de expiração (Gatilho C1) - Prazo: {PRAZO_POSTAGEM_HORAS}h...")
    db = conectar_bd()
    protocolos_expirados = []
    
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
        if db and db.is_connected():
            cursor.close()
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