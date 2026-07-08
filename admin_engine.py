# ==============================================================================
# PROJETO: MyGames - Backoffice
# MÓDULO: admin_engine.py
# DATA DE CRIAÇÃO: 30/05/2026
# TÍTULO: Motor de Regras e Integração de Banco de Dados
# FUNÇÃO: Motor de persistência e regras de negócio do painel administrativo.
# Centraliza a execução de queries SQL complexas e o isolamento da camada de dados.
#
# HISTÓRICO DE ALTERAÇÕES:
# - 30/05/2026: Criação do motor de dados com as funções de busca de protocolo.
# - 01/06/2026: Adição das funções de CRUD para a gestão do Catálogo Mestre.
# - 01/06/2026: Correção das funções de persistência para a tabela regioes_atendimento.
# - 04/06/2026: Atualização no CRUD do catálogo para suportar gravação da coluna foto_oficial_url.
# - 04/06/2026: Adição da função buscar_produtos_por_nome para alimentar o auto-completar inteligente.
# - 10/06/2026: Atualização da função obter_cabecalho_protocolo com LEFT JOIN de status.
# - 10/06/2026: Criação das funções buscar_status_ativos e atualizar_status_protocolo 
#               para suportar o novo workflow (Esteira) de Gestão de Protocolos.
# - 10/06/2026: Adição de obter_resumo_esteira e obter_protocolos_por_status para painel de gavetas.
# - 10/06/2026: Inclusão do campo valor_total_pix na query de obter_cabecalho_protocolo.
# - 11/06/2026: Correção em obter_itens_protocolo (LEFT JOIN e Alias de colunas) para interface Cockpit.
# - 11/06/2026: Atualização em atualizar_status_protocolo para suportar persistência do valor_avaliado.
# - 11/06/2026: Inclusão do campo valor_avaliado na query de obter_cabecalho_protocolo.
# - 11/06/2026: Correção em obter_protocolos_por_status (LEFT JOIN clientes_usuarios) para evitar sumiço de dados.
# - 11/06/2026: Adição de obter_todos_protocolos_listagem para integrar com template de listagem.
# - 12/06/2026: Implementação de filtro em obter_todos_protocolos_listagem para ocultar protocolos encerrados (ID 9).
# - 12/06/2026: Atualização em obter_cabecalho_protocolo para buscar data_status_atual da tabela de histórico.
# - 12/06/2026: Adição do parâmetro admin_id e injeção do INSERT na tabela historico_status_protocolo.
# - 15/06/2026: Adição das funções de persistência (get_categorias, upsert_categoria) para a tabela categorias.
# - 15/06/2026: Adição das funções de persistência (get_canais, upsert_canal) para a tabela canais_aquisicao.
# - 15/06/2026: Correção no schema de canais_aquisicao (nome_exibicao) e geração automática de slug_tecnico.
# - 15/06/2026: Adição das funções de persistência (obter_todos_status, upsert_status) para status_protocolos.
# - 15/06/2026: Adição das funções de persistência (obter_todas_perguntas, upsert_pergunta) para perguntas_conservacao.
# - 15/06/2026: Adição das funções 'obter_opcoes_estado' e 'upsert_opcao_estado'.
# - 15/06/2026: Correção na query SQL de 'upsert_opcao_estado' para utilizar a coluna 'descricao' em vez de 'nome_estado'.
# - 15/06/2026: Adição das funções obter_todos_usuarios, atualizar_permissoes_usuario e registrar_novo_usuario 
#               para suportar o fluxo de Auto-Cadastro e Aprovação de Usuários Admin.
# - 15/06/2026: Adição das funções obter_dados_empresa e salvar_dados_empresa para gerenciar os dados corporativos.
# - 20/06/2026: Implementação de sanitização de dados (remoção de máscaras) na função salvar_dados_empresa.
# - 25/06/2026: Adição da função enviar_email_recuperacao para suporte ao fluxo de recuperação de senha via SMTP.
# - 25/06/2026: Inclusão do cliente_email na query e nova função enviar_email_status_pericia para notificar o usuário final.
# - 25/06/2026: Adição de trava em enviar_email_status_pericia para forçar o valor = 0 caso o status seja Negado ou Recusado.
# - 25/06/2026: Inclusão da biblioteca werkzeug.security e das funções validar_senha_atual e atualizar_senha_usuario.
# - 26/06/2026: Dinamização do nome fantasia (via obter_dados_empresa) nos cabeçalhos e assinaturas de e-mail.
# - 26/06/2026: Conversão dos templates de e-mail de status (Aprovado, Parcial e Negado) para HTML rico com busca de itens do protocolo.
# - 26/06/2026: Inclusão das bibliotecas base64, requests e logging, e criação da função consultar_historico_rastreio para a API REST dos Correios.
# - 26/06/2026: Inclusão dos campos de endereço completo, CEP e bairro na query da função obter_cabecalho_protocolo.
# - 02/07/2026: Atualização da engine para ler e persistir o novo campo recebido_fisicamente nas operações da esteira.
# - 04/07/2026: Refatoração inteligente do e-mail de triagem: Substituição da função enviar_email_divergencia_recebimento 
#               por enviar_email_triagem_recebimento para disparar notificação com texto adaptável (100% sucesso ou faltantes).
# - 05/07/2026: Refatoração Backend: Substituição da coluna textual status_item pela flag numérica status_laudo_id. 
#               Otimização das consultas de banco e regras de disparo de e-mails usando lógica estrita de flags (1, 2, 3).
# - 05/07/2026: Atualização do e-mail de perícia: Inclusão de formatação em negrito/maiúsculo
#               para "DEPRECIAÇÃO PARCIAL" e adição do botão Call-to-Action "RESPONDER AVALIAÇÃO".
# - 05/07/2026: Adição da função obter_relatorio_sla para gerar o Relatório de Aging 
#               com cálculo dinâmico de DATEDIFF via banco de dados.
# - 07/07/2026: Enriquecimento da query na função obter_relatorio_sla com adição de colunas do cliente 
#               (whatsapp, endereço completo) e rastreio, preparando os dados para a exportação otimizada.
# ==============================================================================
import mysql.connector
import os
import json
import re
import unicodedata
import smtplib
import base64
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr 
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

# Configuração de log para validação via terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [RASTREIO] %(levelname)s - %(message)s')

def conectar_bd():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

# --- SERVIÇOS DE E-MAIL ---
def enviar_email_recuperacao(destinatario, nova_senha):
    """
    Envia a senha provisória via SMTP utilizando credenciais do .env.
    """
    try:
        # Busca o nome fantasia da empresa para injetar no e-mail
        dados_empresa = obter_dados_empresa()
        nome_empresa = dados_empresa['nome_fantasia'] if dados_empresa and 'nome_fantasia' in dados_empresa else "MyGames"

        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASS")
        smtp_server = os.getenv("EMAIL_HOST")
        smtp_port = int(os.getenv("EMAIL_PORT", 587))

        msg = MIMEMultipart()
        msg['From'] = formataddr((nome_empresa, sender_email))
        msg['To'] = destinatario
        msg['Subject'] = f"{nome_empresa} - Recuperação de Senha Administrativa"

        corpo = f"""
        Olá,
        
        Recebemos uma solicitação de redefinição de senha para sua conta administrativa.
        
        Sua senha provisória é: {nova_senha}
        
        Por favor, acesse o painel e altere sua senha imediatamente após o primeiro login.
        
        Atenciosamente,
        Equipe {nome_empresa}
        """
        
        msg.attach(MIMEText(corpo, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail de recuperação: {e}")
        return False

def enviar_email_status_pericia(destinatario, nome_cliente, numero_protocolo, status_nome, laudo_tecnico, valor_avaliado, itens_avaliados=None, codigo_rastreio=None, status_rastreio=None):
    """
    Envia notificação em HTML ao usuário sobre a decisão da perícia técnica.
    Formata o e-mail dinamicamente separando status de 'Não Recebido' de 'Reprovado' via numeração de flags.
    """
    try:
        dados_empresa = obter_dados_empresa()
        nome_empresa = dados_empresa['nome_fantasia'] if dados_empresa and 'nome_fantasia' in dados_empresa else "MyGames"

        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASS")
        smtp_server = os.getenv("EMAIL_HOST")
        smtp_port = int(os.getenv("EMAIL_PORT", 587))

        slug_status = unicodedata.normalize('NFKD', status_nome).encode('ASCII', 'ignore').decode('utf-8').lower()
        laudo_formatado = laudo_tecnico.replace('\n', '<br>') if laudo_tecnico else 'Não informado.'

        if 'negado' in slug_status or 'recusado' in slug_status or 'reprovado' in slug_status:
            valor_avaliado = 0.0

        html_itens = "<strong>AVALIAÇÃO DOS ÍTENS DA VENDA:</strong><br><br>"
        
        if itens_avaliados:
            for item in itens_avaliados:
                nome_produto = item.get('nome_produto', 'Produto não identificado')
                valor_original = float(item.get('valor_pix_unitario', 0.0))
                
                valor_final_bd = item.get('valor_final_pix')
                valor_final = float(valor_final_bd) if valor_final_bd is not None else valor_original
                
                motivo_recusa = item.get('motivo_recusa', '')
                recebido_fisicamente = item.get('recebido_fisicamente')
                status_laudo_id = item.get('status_laudo_id')
                
                status_exibicao = ""
                laudo_exibicao = ""

                # SEPARAÇÃO DE REGRAS USANDO FLAGS (1=Aprovado, 2=Parcial, 3=Negado, Físico=0/1)
                if recebido_fisicamente == 0:
                    status_exibicao = " - <span style='color: #dc3545;'>NÃO RECEBIDO</span>"
                    valor_final = 0.0
                elif status_laudo_id == 3:
                    status_exibicao = " - <span style='color: #dc3545;'>REPROVADO</span>"
                    valor_final = 0.0
                    if motivo_recusa:
                        laudo_exibicao = f"<strong>Laudo Técnico:</strong> <span style='color: #888;'>{motivo_recusa}</span><br>"
                elif status_laudo_id == 2:
                     status_exibicao = " - <span style='color: #fd7e14;'>APROVAÇÃO PARCIAL</span>"
                     if motivo_recusa:
                        laudo_exibicao = f"<strong>Laudo Técnico:</strong> <span style='color: #888;'>{motivo_recusa}</span><br>"
                else: # status_laudo_id == 1 ou aprovado base
                    status_exibicao = " - <span style='color: #198754;'>APROVADO</span>"

                html_itens += f"<div style='border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 10px;'>"
                html_itens += f"<strong>Produto:</strong> {nome_produto}{status_exibicao}<br>"
                html_itens += f"<strong>Valor Original Sugerido:</strong> R$ {valor_original:.2f}<br>"
                html_itens += f"<strong>Valor Final Avaliado:</strong> <strong>R$ {valor_final:.2f}</strong><br>"
                html_itens += laudo_exibicao
                html_itens += f"</div>"
            
            # TOTALIZADOR DA AVALIAÇÃO
            html_itens += f"<div style='margin-top: 15px; padding-top: 10px; border-top: 2px solid #ccc;'>"
            html_itens += f"<strong style='font-size: 16px; color: #000;'>VALOR TOTAL DA AVALIAÇÃO: R$ {float(valor_avaliado):.2f}</strong>"
            html_itens += f"</div>"
        else:
            html_itens += "Nenhum detalhe de item disponível."
            
        bloco_rastreio = ""
        if codigo_rastreio:
            bloco_rastreio = f"""
            <p style="margin-top: 0;"><strong>Código de Rastreio:</strong> {codigo_rastreio}<br>
            <strong>Status do Transporte:</strong> {status_rastreio if status_rastreio else 'Sem atualizações'}</p>
            """

        corpo_html = ""

        if 'parcial' in slug_status:
            # Recupera e-mail de contato para o link "Responder"
            dados_empresa = obter_dados_empresa()
            email_resposta = dados_empresa.get('email_contato', sender_email)
            
            corpo_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.5;">
                <p>Olá {nome_cliente},</p>
                <p>Muito obrigado por realizar a venda de seu Game Usado para a <strong>{nome_empresa}</strong>!</p>
                <p>O seu processo de venda foi analisado e o Laudo Técnico de cada item está concluído.</p>
                <p style="margin-bottom: 5px;"><strong>Protocolo:</strong> {numero_protocolo}</p>
                {bloco_rastreio}
                <br>
                {html_itens}
                <p style="margin-top: 20px;">Como pode notar no laudo acima, alguns de seus itens foram <strong>APROVADOS</strong> na perícia técnica enquanto outros sofreram <strong>DEPRECIAÇÃO PARCIAL</strong> ou foram <strong>REPROVADOS</strong>.</p>
                
                <p>Caso esteja de acordo com a nova avaliação responder este e-mail com a palavra: <strong>APROVADO</strong>!</p>
                
                <a href="mailto:{email_resposta}?subject=Re: Protocolo #{numero_protocolo}&body=APROVADO" 
                   style="background-color: #198754; color: #ffffff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                   RESPONDER AVALIAÇÃO
                </a>
                
                <p style="margin-top: 20px;">Nossa equipe entrará em contato com você para definirmos o que fazer com os ítens reprovados para que possamos seguir com o PAGAMENTO!</p>
                <p>Está sendo um grande prazer fazer negócio com você e tê-lo como nosso cliente.</p>
                <br>
                <p>Atenciosamente,<br>Equipe <strong>{nome_empresa}</strong></p>
            </div>
            """

        elif 'negado' in slug_status or 'recusado' in slug_status or 'reprovado' in slug_status:
            corpo_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.5;">
                <p>Olá {nome_cliente},</p>
                <p>Muito obrigado por realizar a sua cotação de venda de seu Game Usado para a <strong>{nome_empresa}</strong>!</p>
                <p>O seu processo de venda foi analisado e o Laudo Técnico de cada item está concluído.</p>
                <p style="margin-bottom: 5px;"><strong>Protocolo:</strong> {numero_protocolo}</p>
                {bloco_rastreio}
                <br>
                {html_itens}
                <p style="margin-top: 20px;">Infelizmente, <strong>TODOS</strong> os seus itens foram <strong>REPROVADOS</strong> na perícia técnica. O Laudo individual acima explica o que aconteceu.</p>
                <p>Nossa equipe entrará em contato com você para definirmos como podemos avançar com a nossa negociação ou para acertar detalhes da devolução dos produtos para você!</p>
                <br>
                <p>Atenciosamente,<br>Equipe <strong>{nome_empresa}</strong></p>
            </div>
            """

        else: # TOTALMENTE APROVADO
            corpo_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.5;">
                <p>Olá {nome_cliente},</p>
                <p>Muito obrigado por realizar a venda de seu Game Usado para a <strong>{nome_empresa}</strong>!</p>
                <p>O seu processo de venda foi analisado e o Laudo Técnico de cada item está concluído.</p>
                <p style="margin-bottom: 5px;"><strong>Protocolo:</strong> {numero_protocolo}</p>
                {bloco_rastreio}
                <br>
                {html_itens}
                <p style="margin-top: 20px;">Todos os seus itens aprovados na perícia técnica estão marcados como <strong>APROVADOS</strong> e vamos realizar o PAGAMENTO destes itens em até 48 horas úteis.</p>
                <p>Foi um grande prazer fazer negócio com você e tê-lo como nosso cliente.</p>
                <br>
                <p>Atenciosamente,<br>Equipe <strong>{nome_empresa}</strong></p>
            </div>
            """

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((nome_empresa, sender_email))
        msg['To'] = destinatario
        msg['Subject'] = f"{nome_empresa} - Atualização do Protocolo #{numero_protocolo}"
        
        msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail de status da perícia (HTML): {e}")
        return False


def enviar_email_triagem_recebimento(destinatario, nome_cliente, numero_protocolo, itens_avaliados, valor_avaliado, codigo_rastreio=None, status_rastreio=None):
    """
    Envia notificação do resultado da triagem física.
    Adapta o texto dinamicamente para celebrar 100% de recebimento ou alertar sobre divergências.
    Posiciona o código de rastreio imediatamente abaixo do número do protocolo.
    """
    try:
        dados_empresa = obter_dados_empresa()
        nome_empresa = dados_empresa['nome_fantasia'] if dados_empresa and 'nome_fantasia' in dados_empresa else "MyGames"

        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASS")
        smtp_server = os.getenv("EMAIL_HOST")
        smtp_port = int(os.getenv("EMAIL_PORT", 587))

        itens_faltantes = 0
        html_itens = "<strong>CONFERÊNCIA DOS ITENS ENVIADOS NA CAIXA:</strong><br><br>"
        
        for item in itens_avaliados:
            nome_produto = item.get('nome_produto', 'Produto não identificado')
            recebido_fisicamente = item.get('recebido_fisicamente')
            status_laudo_id = item.get('status_laudo_id')
            
            # Avalia ausências usando flags diretas em vez de texto
            if recebido_fisicamente == 0 or status_laudo_id == 3:
                itens_faltantes += 1
                html_itens += f"<span style='color: #dc3545;'><strong>Produto: {nome_produto} - ITEM NÃO RECEBIDO OU NEGADO NA CAIXA</strong></span><br><br>"
            else:
                html_itens += f"Produto: {nome_produto} - Recebido com Sucesso<br><br>"

        # BLOCO DE RASTREIO LOGÍSTICO (Limpo e formatado para colar no Protocolo)
        bloco_rastreio = ""
        if codigo_rastreio:
            bloco_rastreio = f"""
            <p style="margin-top: 0; margin-bottom: 15px;"><strong>Código de Rastreio dos Correios:</strong> {codigo_rastreio}<br>
            <strong>Status do Transporte:</strong> {status_rastreio if status_rastreio else 'Sem atualizações'}</p>
            """

        # Roteamento Dinâmico de Texto (Sucesso vs. Divergência)
        if itens_faltantes > 0:
            texto_resultado = f"""
            <p>No entanto, durante a nossa triagem inicial, notamos que <strong>alguns itens declarados não estavam presentes na embalagem</strong>.</p>
            <br>
            {html_itens}
            <p>O Valor Total do Lote foi recalculado para: <strong>R$ {float(valor_avaliado):.2f}</strong>.</p>
            <p>Nossa equipe técnica seguirá com a avaliação dos itens que foram recebidos com sucesso. Se houve algum engano ou se você enviou o item faltante em outra caixa, por favor, responda este e-mail.</p>
            """
            assunto = f"{nome_empresa} - Divergência no Recebimento - Protocolo #{numero_protocolo}"
        else:
            texto_resultado = f"""
            <p><strong>Excelente notícia!</strong> Conferimos a sua caixa e <strong>todos os itens declarados chegaram perfeitamente</strong>.</p>
            <br>
            {html_itens}
            <p>O Valor Total do Lote permanece: <strong>R$ {float(valor_avaliado):.2f}</strong>.</p>
            <p>Nossa equipe técnica já está seguindo com a avaliação física (Perícia) dos seus itens para liberar o seu pagamento o mais rápido possível.</p>
            """
            assunto = f"{nome_empresa} - Caixa Recebida com Sucesso - Protocolo #{numero_protocolo}"

        corpo_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.5;">
            <p>Olá {nome_cliente},</p>
            <p>Recebemos a sua caixa referente ao processo de venda!</p>
            <p style="margin-bottom: 5px;"><strong>Protocolo:</strong> {numero_protocolo}</p>
            {bloco_rastreio}
            {texto_resultado}
            <br>
            <p>Atenciosamente,<br>Equipe <strong>{nome_empresa}</strong></p>
        </div>
        """

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((nome_empresa, sender_email))
        msg['To'] = destinatario
        msg['Subject'] = assunto
        
        msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail de triagem: {e}")
        return False

# [Funções de Protocolo e Esteira de Status]
def obter_cabecalho_protocolo(protocolo_id):
    db = conectar_bd()
    if not db: return None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT p.id, p.numero_protocolo, p.status, p.status_id, p.laudo_tecnico, p.valor_total_pix, p.valor_avaliado, p.data_criacao, p.codigo_rastreio,
                   c.nome_completo as cliente_nome, c.email as cliente_email, c.whatsapp as cliente_whatsapp, c.chave_pix,
                   c.endereco, c.numero, c.complemento, c.bairro, c.cidade, c.estado_uf, c.cep,
                   s.nome_exibicao as status_nome, s.cor_badge, s.slug_tecnico,
                   IFNULL(
                       (SELECT MAX(data_alteracao) FROM historico_status_protocolo WHERE protocolo_id = p.id),
                       p.data_criacao
                   ) AS data_status_atual
            FROM protocolos_recompra p 
            JOIN clientes_usuarios c ON p.cliente_id = c.id 
            LEFT JOIN status_protocolos s ON p.status_id = s.id
            WHERE p.id = %s
        """
        cursor.execute(query, (protocolo_id,))
        resultado = cursor.fetchone()
        return resultado
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def obter_todos_protocolos_listagem():
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT p.id, p.numero_protocolo, p.valor_total_pix, p.data_criacao,
                   c.nome_completo as cliente_nome, 
                   c.whatsapp as cliente_telefone,
                   s.nome_exibicao as status_nome, 
                   s.cor_badge
            FROM protocolos_recompra p 
            LEFT JOIN clientes_usuarios c ON p.cliente_id = c.id 
            LEFT JOIN status_protocolos s ON p.status_id = s.id
            WHERE p.status_id IS NULL OR p.status_id <> 9
            ORDER BY p.data_criacao DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def obter_itens_protocolo(protocolo_id):
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        # UPDATE MIGRATION: Substituição da coluna status_item para status_laudo_id
        query = """
        SELECT 
            i.id, i.qtd_declarada, i.qtd_recebida, i.status_laudo_id, i.recebido_fisicamente,
            i.fotos_json, i.valor_pix_unitario, i.valor_final_pix, 
            i.comentarios AS descricao_estado, i.motivo_recusa,
            cm.nome_produto,
            cat.nome AS categoria
        FROM itens_periciados i 
        LEFT JOIN catalogo_mestre cm ON i.produto_id = cm.id 
        LEFT JOIN categorias cat ON cm.categoria_id = cat.id
        WHERE i.protocolo_id = %s
    """
        cursor.execute(query, (protocolo_id,))
        itens = cursor.fetchall()
        return itens
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def buscar_status_ativos():
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True, buffered=True)
        cursor.execute("""
            SELECT id, slug_tecnico, nome_exibicao, cor_badge 
            FROM status_protocolos 
            WHERE ativo = 1 
            ORDER BY id
        """)
        return cursor.fetchall()
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def atualizar_status_protocolo(protocolo_id, status_id, laudo_tecnico, valor_avaliado=None, admin_id=None, payload_itens=None):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        
        # 1. Atualiza o status do protocolo principal
        if valor_avaliado is not None:
            query = """
                UPDATE protocolos_recompra 
                SET status_id = %s, laudo_tecnico = %s, valor_avaliado = %s
                WHERE id = %s
            """
            cursor.execute(query, (status_id, laudo_tecnico, valor_avaliado, protocolo_id))
        else:
            query = """
                UPDATE protocolos_recompra 
                SET status_id = %s, laudo_tecnico = %s 
                WHERE id = %s
            """
            cursor.execute(query, (status_id, laudo_tecnico, protocolo_id))
            
        # 2. Insere na tabela de histórico
        if admin_id and status_id:
            query_log = """
                INSERT INTO historico_status_protocolo (protocolo_id, status_id, usuario_admin_id)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query_log, (protocolo_id, status_id, admin_id))
            
        # 3. Processamento Granular (Salva Recebimento Física, Valores e Laudos via Numeração)
        if payload_itens:
            try:
                itens = json.loads(payload_itens) if isinstance(payload_itens, str) else payload_itens
                for item in itens:
                    id_item = item.get('id_item')
                    recebido = item.get('recebido')
                    novo_valor = item.get('novo_valor')
                    status_laudo = item.get('status_laudo')
                    texto_laudo = item.get('texto_laudo')
                    
                    # Converte o booleano do JSON (True/False) para o formato do banco (1/0)
                    flag_fisica = 1 if recebido else 0
                    qtd_rec = 1 if recebido else 0
                    
                    # Hierarquia Numérica Estrita: 1 (Aprovado), 2 (Parcial), 3 (Negado). NULL se não avaliado.
                    laudo_id = None
                    if status_laudo:
                        if status_laudo == 'negado':
                            laudo_id = 3
                        elif status_laudo == 'parcial':
                            laudo_id = 2
                        elif status_laudo == 'aprovado':
                            laudo_id = 1
                    
                    # UPDATE ATUALIZADO: Persiste o laudo_id ao invés de texto
                    query_item = """
                        UPDATE itens_periciados 
                        SET status_laudo_id = %s, 
                            qtd_recebida = %s, 
                            recebido_fisicamente = %s,
                            valor_final_pix = %s,
                            motivo_recusa = %s
                        WHERE id = %s AND protocolo_id = %s
                    """
                    
                    # Tratamento numérico seguro
                    v_final = float(novo_valor) if novo_valor is not None else None
                    
                    cursor.execute(query_item, (laudo_id, qtd_rec, flag_fisica, v_final, texto_laudo, id_item, protocolo_id))
            except Exception as e:
                print(f"Erro ao processar itens granulares: {e}")

        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao atualizar status do protocolo: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def obter_resumo_esteira():
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT s.id, s.nome_exibicao, s.cor_badge, COUNT(p.id) as total
            FROM status_protocolos s
            LEFT JOIN protocolos_recompra p ON s.id = p.status_id
            WHERE s.ativo = 1
            GROUP BY s.id, s.nome_exibicao, s.cor_badge
            ORDER BY s.id
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def obter_protocolos_por_status(status_id):
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT p.id, p.numero_protocolo, p.valor_total_pix, p.data_criacao,
                   IFNULL(c.nome_completo, 'Cliente Não Vinculado') as cliente_nome,
                   s.nome_exibicao as status_nome
            FROM protocolos_recompra p 
            LEFT JOIN clientes_usuarios c ON p.cliente_id = c.id 
            LEFT JOIN status_protocolos s ON p.status_id = s.id
            WHERE p.status_id = %s
            ORDER BY p.data_criacao ASC
        """
        cursor.execute(query, (status_id,))
        return cursor.fetchall()
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def obter_relatorio_sla(status_id=None, dias_parados=None, numero_protocolo=None):
    """
    Gera o relatório de SLA calculando dinamicamente há quantos dias o protocolo
    está sem movimentação, filtrando por status, dias ou protocolo específico.
    """
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        
        # A query cruza os protocolos com o histórico para encontrar a ÚLTIMA data de alteração
        query = """
            SELECT p.id, p.numero_protocolo, p.valor_total_pix, p.data_criacao, p.codigo_rastreio,
                   IFNULL(c.nome_completo, 'Cliente Não Vinculado') as cliente_nome, 
                   c.whatsapp, c.cep, c.endereco, c.numero, c.complemento, c.bairro, c.cidade, c.estado_uf,
                   s.nome_exibicao as status_nome, s.cor_badge,
                   IFNULL(MAX(h.data_alteracao), p.data_criacao) as data_ultima_alteracao,
                   DATEDIFF(NOW(), IFNULL(MAX(h.data_alteracao), p.data_criacao)) as dias_no_status
            FROM protocolos_recompra p 
            LEFT JOIN clientes_usuarios c ON p.cliente_id = c.id 
            LEFT JOIN status_protocolos s ON p.status_id = s.id
            LEFT JOIN historico_status_protocolo h ON p.id = h.protocolo_id
            WHERE 1=1
        """
        
        params = []
        
        # Filtro 1: Número do Protocolo (Busca flexível)
        if numero_protocolo:
            query += " AND p.numero_protocolo LIKE %s "
            params.append(f"%{numero_protocolo}%")
            
        # Filtro 2: Status Específico
        if status_id:
            query += " AND p.status_id = %s "
            params.append(status_id)
        else:
            # Se não escolheu status, oculta os finalizados (ID 9) por padrão para limpar a tela
            query += " AND (p.status_id IS NULL OR p.status_id <> 9) "
            
        # Fechamento do agrupamento para o MAX(data_alteracao) funcionar
        query += """
            GROUP BY p.id, p.numero_protocolo, p.valor_total_pix, p.data_criacao, p.codigo_rastreio,
                     c.nome_completo, c.whatsapp, c.cep, c.endereco, c.numero, c.complemento, c.bairro, c.cidade, c.estado_uf,
                     s.nome_exibicao, s.cor_badge
        """
        
        # Filtro 3: Dias Parados (Usa HAVING porque é aplicado APÓS o cálculo do DATEDIFF)
        if dias_parados is not None and str(dias_parados).strip() != '':
            query += " HAVING dias_no_status >= %s "
            params.append(int(dias_parados))
            
        # Ordena os mais atrasados (maior SLA) primeiro
        query += " ORDER BY dias_no_status DESC, p.data_criacao ASC "
        
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao gerar relatório SLA: {err}")
        return []
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

# [Funções do Catálogo Mestre]
def obter_catalogo_completo():
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = "SELECT id, nome_produto, categoria_id, plataforma, valor_venda_ref, valor_pix_base, valor_cred_base, ativo, foto_oficial_url FROM catalogo_mestre ORDER BY nome_produto ASC"
        cursor.execute(query)
        resultados = cursor.fetchall()
        return resultados
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def buscar_produtos_por_nome(termo):
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT id, nome_produto, categoria_id, plataforma, 
                   valor_venda_ref, valor_pix_base, valor_cred_base, 
                   ativo, foto_oficial_url 
            FROM catalogo_mestre 
            WHERE nome_produto LIKE %s 
            ORDER BY nome_produto ASC LIMIT 10
        """
        cursor.execute(query, (f"%{termo}%",))
        resultados = cursor.fetchall()
        return resultados
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def obter_categorias():
    return [{'id': 1, 'nome_categoria': 'Consoles'}, {'id': 2, 'nome_categoria': 'Controles'}, {'id': 3, 'nome_categoria': 'Jogos Físicos'}, {'id': 4, 'nome_categoria': 'Acessórios'}]

def salvar_produto_catalogo(produto_id, nome, categoria, plataforma, valor_venda, valor_pix, valor_cred, ativo, foto_url=None):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        if produto_id:
            if foto_url:
                query = "UPDATE catalogo_mestre SET nome_produto = %s, categoria_id = %s, plataforma = %s, valor_venda_ref = %s, valor_pix_base = %s, valor_cred_base = %s, ativo = %s, foto_oficial_url = %s WHERE id = %s"
                cursor.execute(query, (nome, categoria, plataforma, valor_venda, valor_pix, valor_cred, ativo, foto_url, produto_id))
            else:
                query = "UPDATE catalogo_mestre SET nome_produto = %s, categoria_id = %s, plataforma = %s, valor_venda_ref = %s, valor_pix_base = %s, valor_cred_base = %s, ativo = %s WHERE id = %s"
                cursor.execute(query, (nome, categoria, plataforma, valor_venda, valor_pix, valor_cred, ativo, produto_id))
        else:
            query = "INSERT INTO catalogo_mestre (nome_produto, categoria_id, plataforma, valor_venda_ref, valor_pix_base, valor_cred_base, ativo, foto_oficial_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (nome, categoria, plataforma, valor_venda, valor_pix, valor_cred, ativo, foto_url))
            
        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar produto: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

# [Funções de Gestão de Regiões]
def obter_todas_regioes():
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = "SELECT id, cidade, estado_uf, multiplicador_preco, ativo FROM regioes_atendimento ORDER BY cidade ASC"
        cursor.execute(query)
        resultados = cursor.fetchall()
        return resultados
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def salvar_regiao(regiao_id, cidade, estado_uf, multiplicador_preco, ativo):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        if regiao_id:
            query = """
                UPDATE regioes_atendimento 
                SET cidade = %s, estado_uf = %s, multiplicador_preco = %s, ativo = %s
                WHERE id = %s
            """
            cursor.execute(query, (cidade, estado_uf, multiplicador_preco, ativo, regiao_id))
        else:
            query = """
                INSERT INTO regioes_atendimento (cidade, estado_uf, multiplicador_preco, ativo)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (cidade, estado_uf, multiplicador_preco, ativo))
            
        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar região: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

# [Funções de Gestão de Categorias]
def get_categorias():
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = "SELECT id, nome, ativo FROM categorias ORDER BY nome ASC"
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def upsert_categoria(cat_id, nome, ativo):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        if cat_id:
            query = "UPDATE categorias SET nome = %s, ativo = %s WHERE id = %s"
            cursor.execute(query, (nome, ativo, cat_id))
        else:
            query = "INSERT INTO categorias (nome, ativo) VALUES (%s, %s)"
            cursor.execute(query, (nome, ativo))
            
        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar categoria: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

# [Funções de Gestão de Canais de Aquisição]
def get_canais():
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = "SELECT id, nome_exibicao as nome, ativo FROM canais_aquisicao ORDER BY nome_exibicao ASC"
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def upsert_canal(canal_id, nome, ativo):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        
        # Gerando o slug_tecnico dinamicamente (removendo acentos e espaços)
        slug = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
        slug = re.sub(r'[^a-zA-Z0-9]+', '_', slug).strip('_').lower()
        
        if canal_id:
            query = "UPDATE canais_aquisicao SET nome_exibicao = %s, ativo = %s, slug_tecnico = %s WHERE id = %s"
            cursor.execute(query, (nome, ativo, slug, canal_id))
        else:
            query = "INSERT INTO canais_aquisicao (nome_exibicao, slug_tecnico, ativo) VALUES (%s, %s, %s)"
            cursor.execute(query, (nome, slug, ativo))
            
        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar canal de aquisição: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

# [Funções de Gestão de Status de Protocolos]
def obter_todos_status():
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = "SELECT id, slug_tecnico, nome_exibicao, cor_badge, ativo FROM status_protocolos ORDER BY id ASC"
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def upsert_status(status_id, nome_exibicao, cor_badge, ativo):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        
        # Gerando o slug_tecnico dinamicamente a partir do nome
        slug = unicodedata.normalize('NFKD', nome_exibicao).encode('ASCII', 'ignore').decode('utf-8')
        slug = re.sub(r'[^a-zA-Z0-9]+', '_', slug).strip('_').lower()
        
        if status_id:
            query = "UPDATE status_protocolos SET nome_exibicao = %s, slug_tecnico = %s, cor_badge = %s, ativo = %s WHERE id = %s"
            cursor.execute(query, (nome_exibicao, slug, cor_badge, ativo, status_id))
        else:
            query = "INSERT INTO status_protocolos (nome_exibicao, slug_tecnico, cor_badge, ativo) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (nome_exibicao, slug, cor_badge, ativo))
            
        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar status de protocolo: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

# [Funções de Gestão de Opções de Estado]
def obter_opcoes_estado(categoria_id):
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = "SELECT * FROM opcoes_estado WHERE categoria_id = %s ORDER BY id ASC"
        cursor.execute(query, (categoria_id,))
        return cursor.fetchall()
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def upsert_opcao_estado(id, cat_id, descricao, dep, extra):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        if id:
            query = """
                UPDATE opcoes_estado 
                SET descricao = %s, fator_depreciacao = %s, valor_fixo_extra = %s 
                WHERE id = %s
            """
            cursor.execute(query, (descricao, dep, extra, id))
        else:
            query = """
                INSERT INTO opcoes_estado (categoria_id, descricao, fator_depreciacao, valor_fixo_extra) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (cat_id, descricao, dep, extra))
        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar opção de estado: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

# [Funções de Gestão de Perguntas de Conservação]
def obter_todas_perguntas():
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT p.id, p.texto_pergunta, p.categoria_id, p.tipo_resposta, p.impacto_valor,
                   c.nome AS nome_categoria
            FROM perguntas_conservacao p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            ORDER BY c.nome, p.id
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"Erro ao obter perguntas: {e}")
        return []
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def upsert_pergunta(perg_id, texto, categoria_id, tipo, impacto):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        if perg_id:
            query = """
                UPDATE perguntas_conservacao 
                SET texto_pergunta = %s, categoria_id = %s, tipo_resposta = %s, impacto_valor = %s
                WHERE id = %s
            """
            cursor.execute(query, (texto, categoria_id, tipo, impacto, perg_id))
        else:
            query = """
                INSERT INTO perguntas_conservacao (texto_pergunta, categoria_id, tipo_resposta, impacto_valor)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (texto, categoria_id, tipo, impacto))
        db.commit()
        return True
    except Exception as e:
        print(f"Erro no upsert da pergunta: {e}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

# [Funções de Gestão de Usuários Admin]
def obter_todos_usuarios():
    db = conectar_bd()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT id, nome_completo, usuario_login, email, nivel_acesso, ativo, data_criacao, ultimo_login 
            FROM usuarios_admin 
            ORDER BY nome_completo ASC
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def atualizar_permissoes_usuario(usr_id, nivel_acesso, ativo):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        query = """
            UPDATE usuarios_admin 
            SET nivel_acesso = %s, ativo = %s 
            WHERE id = %s
        """
        cursor.execute(query, (nivel_acesso, ativo, usr_id))
        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao atualizar permissões do usuário: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def registrar_novo_usuario(nome_completo, usuario_login, email, senha_hash):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        query = """
            INSERT INTO usuarios_admin (nome_completo, usuario_login, email, senha_hash, nivel_acesso, ativo, data_criacao)
            VALUES (%s, %s, %s, %s, 'OPERADOR', 0, NOW())
        """
        cursor.execute(query, (nome_completo, usuario_login, email, senha_hash))
        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao registrar novo usuário: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def validar_senha_atual(admin_id, senha_atual):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT senha_hash FROM usuarios_admin WHERE id = %s", (admin_id,))
        usuario = cursor.fetchone()
        
        # Verifica se o usuário existe e se a senha digitada bate com o hash salvo
        if usuario and check_password_hash(usuario['senha_hash'], senha_atual):
            return True
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def atualizar_senha_usuario(admin_id, nova_senha):
    db = conectar_bd()
    if not db: return False
    try:
        cursor = db.cursor()
        senha_hash = generate_password_hash(nova_senha)
        
        # Atualiza a senha e retira a trava de segurança (requer_nova_senha = 0)
        query = """
            UPDATE usuarios_admin 
            SET senha_hash = %s, requer_nova_senha = 0 
            WHERE id = %s
        """
        cursor.execute(query, (senha_hash, admin_id))
        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao atualizar senha do usuário: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

# [Funções de Gestão de Dados Corporativos]
def obter_dados_empresa():
    db = conectar_bd()
    if not db: return None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM dados_empresa WHERE id = 1")
        return cursor.fetchone()
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

def salvar_dados_empresa(dados):
    db = conectar_bd()
    if not db: return False
    try:
        # Limpeza das máscaras antes de persistir no banco (apenas números)
        if dados.get('cnpj'):
            dados['cnpj'] = re.sub(r'\D', '', str(dados['cnpj']))
        if dados.get('cep'):
            dados['cep'] = re.sub(r'\D', '', str(dados['cep']))
        if dados.get('telefone_contato'):
            dados['telefone_contato'] = re.sub(r'\D', '', str(dados['telefone_contato']))

        cursor = db.cursor()
        query = """
            INSERT INTO dados_empresa (id, razao_social, nome_fantasia, cnpj, cep, logradouro, numero, complemento, bairro, cidade, estado_uf, telefone_contato, email_contato)
            VALUES (1, %(razao_social)s, %(nome_fantasia)s, %(cnpj)s, %(cep)s, %(logradouro)s, %(numero)s, %(complemento)s, %(bairro)s, %(cidade)s, %(estado_uf)s, %(telefone_contato)s, %(email_contato)s)
            ON DUPLICATE KEY UPDATE
            razao_social = VALUES(razao_social),
            nome_fantasia = VALUES(nome_fantasia),
            cnpj = VALUES(cnpj),
            cep = VALUES(cep),
            logradouro = VALUES(logradouro),
            numero = VALUES(numero),
            complemento = VALUES(complemento),
            bairro = VALUES(bairro),
            cidade = VALUES(cidade),
            estado_uf = VALUES(estado_uf),
            telefone_contato = VALUES(telefone_contato),
            email_contato = VALUES(email_contato)
        """
        cursor.execute(query, dados)
        db.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar dados da empresa: {err}")
        db.rollback()
        return False
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()


# --- INTEGRAÇÃO CORREIOS (LOGÍSTICA REVERSA) ---

def consultar_historico_rastreio(codigo_rastreio):
    """
    Consulta o histórico de eventos de um objeto na API REST Oficial dos Correios (SRO).
    """
    ambiente = os.getenv('CORREIOS_AMBIENTE', 'homologacao')
    
    # 1. Interceptador Mock (Fake) para testes locais no Admin
    if ambiente == "fake":
        logging.info(f"MODO FAKE ATIVADO: Simulando rastreio para o código {codigo_rastreio}")
        return [
            {"data": "26/06/2026 14:30", "local": "Unidade de Tratamento - São Paulo/SP", "status": "Objeto em trânsito - por favor aguarde"},
            {"data": "26/06/2026 10:00", "local": "Agência dos Correios - São Paulo/SP", "status": "Objeto postado pelo cliente"},
            {"data": "25/06/2026 15:45", "local": "Sistema MyGames", "status": "Logística Reversa Gerada"}
        ]

    if not codigo_rastreio:
        return []

    usuario = os.getenv('CORREIOS_USER')
    senha = os.getenv('CORREIOS_PASS')
    cartao_postagem = os.getenv('CORREIOS_CARTAO_POSTAGEM')
    
    if not all([usuario, senha, cartao_postagem]):
        logging.error("Credenciais dos Correios incompletas no arquivo .env do Admin.")
        return []

    try:
        # 2. Geração do Token de Autenticação (Bearer Token)
        url_token = "https://api.correios.com.br/token/v1/autentica/cartaopostagem"
        auth_string = f"{usuario}:{senha}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

        headers_token = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/json"
        }
        
        payload_token = {"numero": cartao_postagem}
        
        resp_token = requests.post(url_token, json=payload_token, headers=headers_token, timeout=10)
        
        if resp_token.status_code not in (200, 201):
            logging.error(f"Falha na autenticação dos Correios: HTTP {resp_token.status_code} - {resp_token.text}")
            return []
            
        token = resp_token.json().get('token')

        # 3. Consulta de Rastreio (SRO)
        url_sro = f"https://api.correios.com.br/sro-rastro/v1/objetos/{codigo_rastreio}?resultado=T"
        headers_sro = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        resp_sro = requests.get(url_sro, headers=headers_sro, timeout=15)
        
        if resp_sro.status_code == 200:
            dados_sro = resp_sro.json()
            eventos_formatados = []
            
            # O JSON retorna uma lista de objetos pesquisados. Pegamos o primeiro.
            objetos = dados_sro.get('objetos', [])
            if objetos and 'eventos' in objetos[0]:
                eventos_crus = objetos[0]['eventos']
                
                # Parse dos eventos para um formato simplificado e limpo para o front-end
                for evento in eventos_crus:
                    cidade = evento.get('unidade', {}).get('endereco', {}).get('cidade', '')
                    uf = evento.get('unidade', {}).get('endereco', {}).get('uf', '')
                    local = f"{cidade}/{uf}" if cidade and uf else evento.get('unidade', {}).get('nome', 'Local não informado')
                    
                    eventos_formatados.append({
                        "data": evento.get('dtHrCriado', '').replace('T', ' ')[:16], # Formata Data e Hora
                        "local": local,
                        "status": evento.get('descricao', 'Status Indefinido')
                    })
                
                logging.info(f"Rastreio do código {codigo_rastreio} obtido com sucesso.")
                return eventos_formatados
            else:
                logging.warning(f"Nenhum evento encontrado para o rastreio {codigo_rastreio}.")
                return []
        else:
            logging.error(f"Erro na consulta do rastreio: HTTP {resp_sro.status_code}")
            return []

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de conexão com a API dos Correios: {e}")
        return []
    except Exception as e:
        logging.error(f"Erro interno no processamento do rastreio: {e}")
        return []