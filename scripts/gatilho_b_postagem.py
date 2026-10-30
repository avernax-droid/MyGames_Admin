# ==============================================================================
# PROJETO: MyGames - Backoffice
# MÓDULO: scripts/gatilho_b_postagem.py
# DATA DE CRIAÇÃO: Outubro/2026
# TÍTULO: Varredura de Postagem (Gatilho B)
# FUNÇÃO: Script autónomo (Cronjob) para verificar status logístico de protocolos 
# aguardando envio. Consulta a API REST dos Correios em lote. Caso o status mude
# para "Postado", dispara o Webhook (Gatilho B) para o Agente de WhatsApp e 
# avança o protocolo para o status 2 (Produto Recebido) no banco de dados.
# HISTÓRICO DE ALTERAÇÕES:
# - 30/10/2026: Adição do parâmetro de ambiente PRAZO_POSTAGEM_HORAS e otimização 
#   da query SQL para limitar a busca a protocolos criados dentro desse limite.
# ==============================================================================

import os
import sys
import base64
import requests
import json
import logging
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Define caminhos e carrega .env do Admin
caminho_env_admin = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
load_dotenv(dotenv_path=caminho_env_admin)

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [GATILHO_B] %(levelname)s - %(message)s'
)

# Credenciais Banco de Dados
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# Credenciais Correios
CLIENT_ID = os.getenv('CORREIOS_CLIENT_ID', '').strip()
CLIENT_SECRET = os.getenv('CORREIOS_CLIENT_SECRET', '').strip()
CARTAO_POSTAGEM = os.getenv('CORREIOS_CARTAO_POSTAGEM', '').strip()
URL_TOKEN = "https://api.correios.com.br/token/v1/autentica/cartaopostagem"
URL_SRO = "https://api.correios.com.br/srorastro/v1/objetos"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

TOKEN_CACHE = {"token": None, "expira_em": None}

# Credenciais Webhook (Gatilho B) e Regras de Negócio
WEBHOOK_URL = os.getenv('WEBHOOK_AGENTE_URL_B')
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

def obter_token_correios():
    global TOKEN_CACHE
    
    if not CLIENT_ID or not CLIENT_SECRET:
        logging.error("Credenciais CORREIOS_CLIENT_ID ou CORREIOS_CLIENT_SECRET ausentes no .env")
        sys.exit(1)

    if TOKEN_CACHE["token"] and TOKEN_CACHE["expira_em"] > datetime.now() + timedelta(minutes=5):
        return TOKEN_CACHE["token"]

    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }
    
    payload = {"numero": CARTAO_POSTAGEM}
    
    try:
        resp = requests.post(URL_TOKEN, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        token = data.get("token") or data.get("access_token")
        TOKEN_CACHE["token"] = token
        TOKEN_CACHE["expira_em"] = datetime.now() + timedelta(seconds=data.get("expires_in", 28800))
        return token
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro na API de autenticação Correios: {e}")
        sys.exit(1)

def consultar_sro_lote(codigos):
    """Consulta a API SRO. Limite prático de envio na query string é geralmente 50 itens."""
    token = obter_token_correios()
    codigos_str = ",".join(codigos)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT
    }
    
    try:
        resp = requests.get(URL_SRO, headers=headers, params={"codigosObjetos": codigos_str, "resultado": "T"}, timeout=30)
        if resp.status_code == 401: # Token expirado
            TOKEN_CACHE["token"] = None
            return consultar_sro_lote(codigos)
            
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.error(f"Falha ao consultar lote na API SRO: {e}")
        return None

def disparar_gatilho_b(numero_protocolo, codigo_rastreio):
    """Envia o POST para a API do Agente de WhatsApp informando o envio."""
    if not WEBHOOK_URL:
        logging.warning("WEBHOOK_AGENTE_URL_B não configurado. Gatilho B não disparado.")
        return False
        
    payload = {
        "evento": "produto_postado",
        "dados": {
            "protocolo": numero_protocolo,
            "codigo_rastreio": codigo_rastreio,
            "ambiente": AMBIENTE
        }
    }
    
    headers = {"Content-Type": "application/json"}
    if TOKEN_AGENTE:
        headers["Authorization"] = f"Bearer {TOKEN_AGENTE}"
        
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        if resp.status_code in [200, 201]:
            logging.info(f"Gatilho B disparado com sucesso para {numero_protocolo}.")
            return True
        else:
            logging.error(f"Falha no Webhook (Gatilho B). Status: {resp.status_code} | Resposta: {resp.text}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Timeout/Erro ao conectar no Webhook do Agente: {e}")
        return False

def avancar_status_local(protocolo_id):
    """Avança o protocolo para Status 2 (Produto Recebido) e regista o histórico."""
    db = conectar_bd()
    try:
        cursor = db.cursor()
        
        query_update = "UPDATE protocolos_recompra SET status_id = 2 WHERE id = %s"
        cursor.execute(query_update, (protocolo_id,))
        
        # ID 1 para o admin fictício 'Sistema' no histórico
        query_log = """
            INSERT INTO historico_status_protocolo (protocolo_id, status_id, usuario_admin_id, data_alteracao)
            VALUES (%s, 2, 1, NOW())
        """
        cursor.execute(query_log, (protocolo_id,))
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

def processar_varredura():
    logging.info("Iniciando varredura diária de postagens (Gatilho B)...")
    db = conectar_bd()
    protocolos_pendentes = {}
    
    try:
        cursor = db.cursor(dictionary=True)
        # Seleciona Status 1 (Aguardando cliente) restrito ao prazo limite parametrizado
        query = """
            SELECT id, numero_protocolo, codigo_rastreio 
            FROM protocolos_recompra 
            WHERE status_id = 1 
              AND codigo_rastreio IS NOT NULL 
              AND codigo_rastreio != ''
              AND data_criacao >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        """
        cursor.execute(query, (PRAZO_POSTAGEM_HORAS,))
        resultados = cursor.fetchall()
        
        for p in resultados:
            protocolos_pendentes[p['codigo_rastreio']] = {
                "id": p['id'], 
                "numero_protocolo": p['numero_protocolo']
            }
    except Exception as e:
        logging.error(f"Erro ao ler banco de dados: {e}")
        sys.exit(1)
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

    if not protocolos_pendentes:
        logging.info("Nenhum protocolo aguardando postagem.")
        return

    lista_codigos = list(protocolos_pendentes.keys())
    logging.info(f"Encontrados {len(lista_codigos)} rastreios aguardando. Consultando Correios...")

    # Fragmenta em pacotes de 50 para evitar sobrecarga ou erro 414 URI Too Long na API dos Correios
    for i in range(0, len(lista_codigos), 50):
        lote_atual = lista_codigos[i:i+50]
        resposta_sro = consultar_sro_lote(lote_atual)
        
        if not resposta_sro or "objetos" not in resposta_sro:
            continue
            
        for obj in resposta_sro["objetos"]:
            cod = obj.get("codObjeto")
            eventos = obj.get("eventos", [])
            
            # Verifica se existe o termo 'postado' em algum evento
            foi_postado = False
            for ev in eventos:
                if 'postado' in ev.get("descricao", "").lower():
                    foi_postado = True
                    break
                    
            if foi_postado and cod in protocolos_pendentes:
                dados_prot = protocolos_pendentes[cod]
                logging.info(f"CONFIRMADO: {cod} (Protocolo {dados_prot['numero_protocolo']}) foi postado.")
                
                # 1. Dispara o Gatilho
                disparar_gatilho_b(dados_prot['numero_protocolo'], cod)
                
                # 2. Atualiza Banco de Dados
                avancar_status_local(dados_prot['id'])
                
    logging.info("Varredura (Gatilho B) finalizada com sucesso.")

if __name__ == "__main__":
    processar_varredura()