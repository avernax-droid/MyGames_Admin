# ==============================================================================
# PROJETO: MyGames
# MÓDULO: scripts/teste_webhook_n8n.py
# DATA CRIAÇÃO: 29/10/2026
# TÍTULO: Teste Isolado de Webhook N8N (Gatilho A)
# FUNÇÃO: Disparar um payload estático para o webhook do agente N8N utilizando
#         os dados de teste exigidos na trava de segurança (Homologação).
# HISTÓRICO:
#   - 29/10/2026: Criação do script de teste isolado.
# ==============================================================================

import os
import json
import requests
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do .env da raiz do projeto (Site)
caminho_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(caminho_env)

# Obtém a URL e o Token do .env
webhook_url = os.getenv("WEBHOOK_AGENTE_URL_A")
token = os.getenv("AGENTE_TOKEN_ENVIO")

def testar_envio_novo_protocolo():
    if not webhook_url or not token:
        print("ERRO: WEBHOOK_AGENTE_URL_A ou AGENTE_TOKEN_ENVIO não configurados no .env")
        return

    # Payload estático exigido pela trava de segurança do Nickolas
    payload = {
        "evento": "novo_protocolo",
        "dados": {
            "protocolo": "TESTE-MYGAMES-HTTP-20261028",
            "cliente": "Nickolas teste de integração",
            "email": "",
            "telefone": "5532998522450",
            "valor_total_cotacao": 450.0,
            "codigo_rastreio": "QA-HTTP-20261028",
            "ambiente": "homologacao",
            "produtos": [
                {
                    "nome": "Console fictício para teste",
                    "quantidade": 1,
                    "valor_unitario": 450.0,
                    "valor_total": 450.0
                }
            ]
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    print(f"Enviando POST para: {webhook_url}")
    print(f"Com o Token: Bearer {token[:5]}...{token[-5:]}")
    print("Aguardando resposta...\n")

    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        
        print(f"Status Code HTTP: {response.status_code}")
        print("Resposta do Servidor N8N:")
        try:
            print(json.dumps(response.json(), indent=4, ensure_ascii=False))
        except ValueError:
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Falha ao conectar: {e}")

if __name__ == "__main__":
    testar_envio_novo_protocolo()