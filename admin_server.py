# ==============================================================================
# PROJETO: MyGames - Backoffice
# MÓDULO: admin_server.py
# DATA DE CRIAÇÃO: 30/05/2026
# TÍTULO: Servidor Web e Roteamento Flask
# FUNÇÃO: Servidor Controller principal do painel administrativo.
# Gerencia a autenticação via identidade do usuário, sessão e permissões RBAC.
#
# HISTÓRICO DE ALTERAÇÕES:
# - 30/05/2026: Criação do servidor controller inicial e rotas de autenticação.
# - 01/06/2026: Adição de rotas para gestão (CRUD) de Regiões de Atendimento e Catálogo.
# - 04/06/2026: Adição de rotas AJAX e de upload seguro para o catálogo.
# - 10/06/2026: Criação do pipeline de rotas para a Fila de Trabalho (Esteira) e Cockpit.
# - 11/06/2026: Refatorações AJAX para salvamento de perícia e correções de portas/Docker.
# - 12/06/2026: Injeção de rastreio de auditoria (admin_id) nas atualizações de status.
# - 15/06/2026: Refatoração estrutural de rotas para a subpasta 'configuracoes/'.
# - 15/06/2026: Adição de suporte AJAX (retorno JSON) nas rotas de salvamento de configurações.
# - 15/06/2026: Implementação de Context Processor para injeção global de categorias no menu lateral.
# - 15/06/2026: Refatoração da rota /perguntas para suportar filtro de navegação por <categoria_id>.
# - 15/06/2026: Ajuste na rota '/opcoes_estado/salvar' para suportar JSON via Fetch API.
# - 15/06/2026: Implementação das rotas /usuarios e /usuarios/salvar para gestão da equipe.
# - 15/06/2026: Refatoração da rota raiz (/) para processar o fluxo de Auto-Cadastro com hash de senhas e bloqueio de inativos.
# - 15/06/2026: Adição das rotas /dados_empresa e /dados_empresa/salvar para gestão corporativa (Remetente/Termos).
# - 25/06/2026: Implementação do fluxo de recuperação de senha (Opção 2 - geração de senha provisória).
# - 25/06/2026: Integração real do disparo de e-mail (SMTP) na recuperação de senha.
# - 25/06/2026: Integração de envio automático de e-mail ao cliente nas rotas de alteração de status da perícia.
# - 26/06/2026: Integração da consulta de rastreio da Logística Reversa (Correios) na rota detalhes_protocolo.
# - 27/06/2026: Injeção do historico_rastreio (Correios) na rota de Perícia da Esteira (Cockpit).
# - 30/06/2026: Atualização da rota salvar_pericia_esteira para processar a Perícia Granular.
#               Implementação de gatilho inteligente para e-mail de divergência de recebimento.
# - 02/07/2026: Correção do gatilho de e-mail na salvar_pericia_esteira para usar o novo padrão booleano (recebido_fisicamente).
# - 04/07/2026: Correção de escopo (BugFix) na injeção da variável codigo_rastreio. 
#               Alteração da Regra 1 (E-mail de Triagem) para disparar como 'Recibo de Conferência' sempre que houver alteração de recebimento.
# - 05/07/2026: Criação da rota /monitor-sla (GET) para suportar o painel de auditoria de SLA e Aging de protocolos.
# - 06/07/2026: Ajuste na rota /monitor-sla para abrir painel vazio, exigindo uso de filtros para consulta.
# - 06/07/2026: Refatoração da rota /monitor-sla: Implementação de cabeçalhos anti-cache (no-store) e lógica de busca condicional (apenas com filtros).
# ==============================================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify, make_response
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
import json
import string
import random
from functools import wraps
import requests
from dotenv import load_dotenv
import admin_engine

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Diretório para upload das imagens do catálogo
DIRETORIO_CATALOGO = os.path.join(app.root_path, 'static', 'images', 'catalogo')
os.makedirs(DIRETORIO_CATALOGO, exist_ok=True)

# --- MATRIZ DE PERMISSÕES (RBAC) ---
PERMISSOES = {
    'Administrador': {
        'protocolos': ['read', 'update', 'delete', 'create'],
        'catalogo': ['read', 'update', 'delete', 'create'],
        'regioes': ['read', 'update', 'delete', 'create']
    },
    'Operador': {
        'protocolos': ['read', 'update'],
        'catalogo': ['read'],
        'regioes': []
    }
}

def conectar_bd():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

def requer_permissao(modulo, acao='read'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'admin_id' not in session: return redirect(url_for('login'))
            nivel = session.get('admin_nivel')
            permissoes_nivel = PERMISSOES.get(nivel, {})
            permissoes_modulo = permissoes_nivel.get(modulo, [])
            if acao not in permissoes_modulo:
                flash('Acesso negado.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- INTERCEPTADOR GLOBAL DE SEGURANÇA ---
@app.before_request
def verificar_troca_senha():
    """
    Intercepta todas as requisições. Se o usuário estiver logado com uma senha provisória,
    força o redirecionamento para a tela de alteração de senha.
    """
    if 'admin_id' in session and session.get('requer_troca_senha') == True:
        # Rotas que o usuário PODE acessar enquanto está bloqueado
        rotas_permitidas = ['mudar_senha', 'logout', 'static']
        
        if request.endpoint not in rotas_permitidas:
            flash("Por segurança, você precisa redefinir sua senha provisória antes de acessar o painel.", "error")
            return redirect(url_for('mudar_senha'))

# --- CONTEXT PROCESSOR (INJEÇÃO GLOBAL PARA O BASE.HTML) ---
@app.context_processor
def injetar_dados_globais():
    """Injeta variáveis globalmente em todos os templates renderizados pelo Flask."""
    dados = {'lista_categorias_global': []}
    if 'admin_id' in session:
        try:
            # Disponibiliza as categorias para montar o menu de navegação da barra esquerda
            dados['lista_categorias_global'] = admin_engine.get_categorias()
        except Exception:
            pass
    return dados

# --- ROTAS CORE (COM AUTO-CADASTRO, RECUPERAÇÃO E LOGIN) ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'admin_id' in session: return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        acao = request.form.get('acao', 'login')
        
        # Fluxo de Auto-Cadastro
        if acao == 'registrar':
            nome = request.form.get('nome_completo')
            user_login = request.form.get('usuario_login')
            email = request.form.get('email')
            senha = request.form.get('senha')
            
            if not all([nome, user_login, email, senha]):
                flash('Preencha todos os campos para solicitar acesso.', 'error')
                return render_template('login.html')
                
            senha_hash = generate_password_hash(senha)
            sucesso = admin_engine.registrar_novo_usuario(nome, user_login, email, senha_hash)
            
            if sucesso:
                flash('Solicitação enviada com sucesso! Aguarde a liberação do Administrador.', 'success')
            else:
                flash('Erro ao solicitar acesso. O usuário ou e-mail já pode estar em uso.', 'error')
            return redirect(url_for('login'))
            
        # Fluxo de Recuperação de Senha (Opção 2)
        elif acao == 'recuperar_senha':
            usuario_login = request.form.get('usuario_login')
            
            if not usuario_login:
                flash('Informe a Identidade do Usuário para recuperar a senha.', 'error')
                return redirect(url_for('login'))
                
            db = conectar_bd()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios_admin WHERE usuario_login = %s", (usuario_login,))
            usuario = cursor.fetchone()
            
            if usuario:
                # Gerar senha provisória de 8 caracteres
                caracteres = string.ascii_letters + string.digits + "@#$%"
                senha_provisoria = ''.join(random.choice(caracteres) for _ in range(8))
                senha_hash = generate_password_hash(senha_provisoria)
                
                # Atualizar no banco ativando a flag de requisição de nova senha
                cursor.execute("UPDATE usuarios_admin SET senha_hash = %s, requer_nova_senha = 1 WHERE id = %s", (senha_hash, usuario['id']))
                db.commit()
                
                # Disparo real do e-mail de recuperação
                admin_engine.enviar_email_recuperacao(usuario['email'], senha_provisoria)
            
            db.close()
            
            # Mensagem genérica por segurança (anti-enumeração)
            flash('Se o usuário for válido, uma senha provisória foi enviada para o e-mail cadastrado.', 'success')
            return redirect(url_for('login'))
            
        # Fluxo de Login Tradicional
        else:
            usuario_login = request.form.get('usuario_login')
            senha = request.form.get('senha')
            
            db = conectar_bd()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios_admin WHERE usuario_login = %s", (usuario_login,))
            usuario = cursor.fetchone()
            db.close()
            
            if usuario and check_password_hash(usuario['senha_hash'], senha):
                if usuario['ativo'] == 1:
                    session['admin_id'] = usuario['id']
                    session['admin_nome'] = usuario['nome_completo']
                    session['admin_nivel'] = usuario['nivel_acesso']
                    
                    # Trava de segurança para obrigar a troca da senha provisória
                    session['requer_troca_senha'] = True if usuario.get('requer_nova_senha') == 1 else False
                    
                    return redirect(url_for('dashboard'))
                else:
                    flash('Sua conta está pendente de aprovação pelo Administrador.', 'error')
            else:
                flash('Dados incorretos.', 'error')
                
    return render_template('login.html')

@app.route('/mudar_senha', methods=['GET', 'POST'])
def mudar_senha():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if nova_senha != confirmar_senha:
            flash("A nova senha e a confirmação não coincidem.", "error")
            return render_template('mudar_senha.html')
            
        if admin_engine.validar_senha_atual(session['admin_id'], senha_atual):
            if admin_engine.atualizar_senha_usuario(session['admin_id'], nova_senha):
                session.pop('requer_troca_senha', None)
                return redirect(url_for('dashboard'))
            else:
                flash("Erro ao gravar a nova senha no banco de dados.", "error")
        else:
            flash("A senha atual informada está incorreta.", "error")
            
    return render_template('mudar_senha.html')

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/protocolos')
@requer_permissao('protocolos', 'read')
def listar_protocolos():
    lista_protocolos = admin_engine.obter_todos_protocolos_listagem()
    return render_template('protocolos.html', protocolos=lista_protocolos)

# --- ROTA: MONITOR DE SLA (AGING) ---
@app.route('/monitor-sla', methods=['GET'])
@requer_permissao('protocolos', 'read')
def monitor_sla():
    """
    Controlador do Relatório de SLA (Aging).
    Ajustado para forçar renovação de cache e processar busca apenas com filtros.
    """
    status_id = request.args.get('status_id')
    dias_parados = request.args.get('dias_parados')
    numero_protocolo = request.args.get('numero_protocolo')
    
    # Verifica se algum filtro foi aplicado
    tem_filtro = any([status_id, dias_parados, numero_protocolo])
    
    if status_id and status_id.strip() != '':
        status_id = int(status_id)
    else:
        status_id = None
        
    lista_status = admin_engine.buscar_status_ativos()
    
    # Executa a busca apenas se houver filtro, caso contrário, retorna lista vazia
    if tem_filtro:
        protocolos_atrasados = admin_engine.obter_relatorio_sla(status_id, dias_parados, numero_protocolo)
    else:
        protocolos_atrasados = []
    
    # Cria a resposta e define cabeçalhos para evitar cache do navegador
    response = make_response(render_template('monitor_sla.html',
                           protocolos=protocolos_atrasados,
                           lista_status=lista_status,
                           filtro_status=status_id,
                           filtro_dias=dias_parados,
                           filtro_protocolo=numero_protocolo))
                           
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response

# --- ROTA: FILA DE TRABALHO (ESTEIRA) ---
@app.route('/esteira')
@app.route('/esteira/<int:status_id>')
@requer_permissao('protocolos', 'read')
def esteira_protocolos(status_id=None):
    resumo_status = admin_engine.obter_resumo_esteira()
    
    protocolos_filtrados = []
    if status_id:
        protocolos_filtrados = admin_engine.obter_protocolos_por_status(status_id)
        
    return render_template('esteira.html', 
                           resumo_status=resumo_status, 
                           protocolos=protocolos_filtrados, 
                           status_selecionado=status_id)

# --- ROTA: TELA DE PERÍCIA FOCADA (COCKPIT) ---
@app.route('/esteira/periciar/<int:protocolo_id>')
@requer_permissao('protocolos', 'update')
def periciar_na_esteira(protocolo_id):
    dados_protocolo = admin_engine.obter_cabecalho_protocolo(protocolo_id)
    if not dados_protocolo:
        flash('Protocolo não encontrado.', 'error')
        return redirect(url_for('esteira_protocolos'))
    
    itens_protocolo = admin_engine.obter_itens_protocolo(protocolo_id)
    
    for item in itens_protocolo:
        item['fotos'] = []
        if item.get('fotos_json'):
            try:
                fotos_lista = json.loads(item['fotos_json'])
                if isinstance(fotos_lista, list):
                    item['fotos'] = fotos_lista
            except json.JSONDecodeError:
                pass
                
    lista_status = admin_engine.buscar_status_ativos()
    
    # NOVA LÓGICA: Consulta de Rastreio para o painel de perícia (Cockpit)
    historico_rastreio = []
    codigo_rastreio = dados_protocolo.get('codigo_rastreio')
    if codigo_rastreio:
        historico_rastreio = admin_engine.consultar_historico_rastreio(codigo_rastreio)
    
    return render_template('pericia_esteira.html', 
                           protocolo=dados_protocolo, 
                           itens=itens_protocolo, 
                           lista_status=lista_status,
                           historico_rastreio=historico_rastreio)

# --- ROTA: SALVAR DECISÃO DA PERÍCIA (INCLUI DISPARO DE E-MAIL E GRANULARIDADE) ---
@app.route('/esteira/salvar_pericia/<int:protocolo_id>', methods=['POST'])
@requer_permissao('protocolos', 'update')
def salvar_pericia_esteira(protocolo_id):
    status_id = request.form.get('status_id')
    laudo_tecnico = request.form.get('laudo_tecnico')
    valor_avaliado = request.form.get('valor_avaliado')
    payload_itens = request.form.get('payload_itens')
    origem = request.form.get('origem')  # <--- NOVA VARIÁVEL CAPTURADA
    
    admin_id = session.get('admin_id')
    is_ajax = request.headers.get('Accept') == 'application/json'

    if not status_id or not valor_avaliado:
        if is_ajax:
            return jsonify({'sucesso': False, 'mensagem': 'Status e Valor Avaliado são obrigatórios.'})
        flash('Status e Valor Avaliado são obrigatórios.', 'error')
        return redirect(url_for('periciar_na_esteira', protocolo_id=protocolo_id))

    # 1. Tira uma "foto" do banco antes de atualizar para rastrear o que mudou
    itens_antigos = admin_engine.obter_itens_protocolo(protocolo_id)

    # 2. Atualiza o banco de dados (salvando o booleano de recebimento granular e valores)
    sucesso = admin_engine.atualizar_status_protocolo(protocolo_id, status_id, laudo_tecnico, valor_avaliado, admin_id, payload_itens)

    if sucesso:
        protocolo_atualizado = admin_engine.obter_cabecalho_protocolo(protocolo_id)
        if protocolo_atualizado and protocolo_atualizado.get('cliente_email'):
            slug = protocolo_atualizado.get('slug_tecnico', '').lower() if protocolo_atualizado.get('slug_tecnico') else ''
            
            # -------------------------------------------------------------
            # CORREÇÃO: CONSULTA DE RASTREIO GLOBAL PARA USO NAS REGRAS 1 E 2
            # -------------------------------------------------------------
            codigo_rastreio = protocolo_atualizado.get('codigo_rastreio')
            status_rastreio_reversa = ""
            if codigo_rastreio:
                historico = admin_engine.consultar_historico_rastreio(codigo_rastreio)
                if historico:
                     status_rastreio_reversa = historico[0].get('status', '')
            
            # REGRA 1: Email de Triagem de Recebimento (Sucesso Total ou Divergência)
            if payload_itens:
                try:
                    itens_json = json.loads(payload_itens)
                    teve_nova_triagem = False
                    
                    for novo_item in itens_json:
                        # Extrai do HTML se o botão foi clicado e marcou o produto como recebido ou não (True/False)
                        flag_nova_recebido = 1 if novo_item.get('recebido') else 0
                        
                        for antigo in itens_antigos:
                            if str(antigo['id']) == str(novo_item['id_item']):
                                # Se a situação física mudou comparada à memória do BD, houve triagem.
                                if antigo.get('recebido_fisicamente') != flag_nova_recebido:
                                    teve_nova_triagem = True
                                break
                                    
                    # O email será disparado assim que o operador "Salvar Lote" contendo novas checagens
                    if teve_nova_triagem:
                        itens_atualizados = admin_engine.obter_itens_protocolo(protocolo_id)
                        admin_engine.enviar_email_triagem_recebimento(
                            destinatario=protocolo_atualizado['cliente_email'],
                            nome_cliente=protocolo_atualizado['cliente_nome'],
                            numero_protocolo=protocolo_atualizado['numero_protocolo'],
                            itens_avaliados=itens_atualizados,
                            valor_avaliado=protocolo_atualizado['valor_avaliado'],
                            codigo_rastreio=codigo_rastreio,           
                            status_rastreio=status_rastreio_reversa    
                        )
                except Exception as e:
                    print(f"Erro ao processar gatilho de email de triagem: {e}")
            
            # REGRA 2: Email Final da Perícia Técnica
            if 'aprovado' in slug or 'negado' in slug or 'recusado' in slug or 'parcial' in slug:
                itens_atualizados_banco = admin_engine.obter_itens_protocolo(protocolo_id)
                
                admin_engine.enviar_email_status_pericia(
                    destinatario=protocolo_atualizado['cliente_email'],
                    nome_cliente=protocolo_atualizado['cliente_nome'],
                    numero_protocolo=protocolo_atualizado['numero_protocolo'],
                    status_nome=protocolo_atualizado['status_nome'],
                    laudo_tecnico=protocolo_atualizado['laudo_tecnico'],
                    valor_avaliado=protocolo_atualizado['valor_avaliado'],
                    itens_avaliados=itens_atualizados_banco,
                    codigo_rastreio=codigo_rastreio,         
                    status_rastreio=status_rastreio_reversa  
                )

    if is_ajax:
        return jsonify({'sucesso': sucesso})

    if not sucesso:
        flash('Erro interno ao salvar a perícia.', 'error')
        return redirect(url_for('periciar_na_esteira', protocolo_id=protocolo_id))

    # --- DESVIO INTELIGENTE (FALLBACK SEM AJAX) ---
    if origem == 'monitor_sla':
        return redirect(url_for('monitor_sla'))
        
    return redirect(url_for('esteira_protocolos'))


@app.route('/protocolos/<int:protocolo_id>')
@requer_permissao('protocolos', 'read')
def detalhes_protocolo(protocolo_id):
    dados_protocolo = admin_engine.obter_cabecalho_protocolo(protocolo_id)
    if not dados_protocolo:
        flash('Protocolo não encontrado.', 'error')
        return redirect(url_for('listar_protocolos'))
    
    itens_protocolo = admin_engine.obter_itens_protocolo(protocolo_id)
    diretorio_uploads = os.getenv("DIRETORIO_UPLOADS_PERICIA", "")
    
    for item in itens_protocolo:
        item['fotos_validadas'] = []
        if item.get('fotos_json'):
            try:
                fotos = json.loads(item['fotos_json'])
                if isinstance(fotos, list):
                    for foto_nome in fotos:
                        caminho_fisico = os.path.join(diretorio_uploads, foto_nome)
                        existe = os.path.exists(caminho_fisico) if diretorio_uploads else False
                        
                        item['fotos_validadas'].append({
                            'nome': foto_nome,
                            'existe_no_disco': existe,
                            'url_estatica': f"/uploads/pericia/{foto_nome}"
                        })
            except json.JSONDecodeError:
                pass
                
    lista_status = admin_engine.buscar_status_ativos()
    
    # NOVA LÓGICA DE CONSULTA AO RASTREIO DA LOGÍSTICA REVERSA
    historico_rastreio = []
    codigo_rastreio = dados_protocolo.get('codigo_rastreio')
    if codigo_rastreio:
        historico_rastreio = admin_engine.consultar_historico_rastreio(codigo_rastreio)
        
    return render_template('detalhes_protocolo.html', 
                           protocolo=dados_protocolo, 
                           itens=itens_protocolo, 
                           lista_status=lista_status,
                           historico_rastreio=historico_rastreio)

@app.route('/protocolos/atualizar_status/<int:protocolo_id>', methods=['POST'])
@requer_permissao('protocolos', 'update')
def atualizar_status_protocolo(protocolo_id):
    status_id = request.form.get('status_id')
    laudo_tecnico = request.form.get('laudo_tecnico')
    
    admin_id = session.get('admin_id')

    if not status_id:
        flash('Status inválido. Selecione uma etapa válida da esteira.', 'error')
        return redirect(url_for('detalhes_protocolo', protocolo_id=protocolo_id))

    sucesso = admin_engine.atualizar_status_protocolo(protocolo_id, status_id, laudo_tecnico, None, admin_id)

    if sucesso:
        # Gatilho de notificação na edição pela listagem geral também
        protocolo_atualizado = admin_engine.obter_cabecalho_protocolo(protocolo_id)
        if protocolo_atualizado and protocolo_atualizado.get('cliente_email'):
            slug = protocolo_atualizado.get('slug_tecnico', '').lower() if protocolo_atualizado.get('slug_tecnico') else ''
            
            if 'aprovado' in slug or 'negado' in slug or 'recusado' in slug or 'parcial' in slug:
                admin_engine.enviar_email_status_pericia(
                    destinatario=protocolo_atualizado['cliente_email'],
                    nome_cliente=protocolo_atualizado['cliente_nome'],
                    numero_protocolo=protocolo_atualizado['numero_protocolo'],
                    status_nome=protocolo_atualizado['status_nome'],
                    laudo_tecnico=protocolo_atualizado['laudo_tecnico'],
                    valor_avaliado=protocolo_atualizado['valor_avaliado']
                )
        flash('Status do protocolo atualizado com sucesso!', 'success')
    else:
        flash('Erro interno ao atualizar o status do protocolo.', 'error')

    return redirect(url_for('detalhes_protocolo', protocolo_id=protocolo_id))

@app.route('/catalogo')
@requer_permissao('catalogo', 'read')
def listar_catalogo():
    produtos = admin_engine.obter_catalogo_completo()
    categorias = admin_engine.obter_categorias()
    return render_template('catalogo.html', produtos=produtos, categorias=categorias)

@app.route('/api/buscar_produtos_nome')
@requer_permissao('catalogo', 'read')
def api_buscar_produtos_nome():
    termo = request.args.get('q', '')
    if not termo or len(termo) < 2:
        return jsonify([])
    produtos = admin_engine.buscar_produtos_por_nome(termo)
    return jsonify(produtos)

@app.route('/catalogo/salvar', methods=['POST'])
@requer_permissao('catalogo', 'update')
def salvar_catalogo():
    produto_id = request.form.get('id')
    nome = request.form.get('nome_produto')
    categoria = request.form.get('categoria_id')
    plataforma = request.form.get('plataforma')
    valor_venda = request.form.get('valor_venda_ref')
    valor_pix = request.form.get('valor_pix_base')
    valor_cred = request.form.get('valor_cred_base')
    ativo = request.form.get('ativo')
    
    produto_id = int(produto_id) if produto_id and produto_id.isdigit() else None
    
    try:
        v_venda = float(valor_venda) if valor_venda else 0.0
        v_pix = float(valor_pix) if valor_pix else 0.0
        v_cred = float(valor_cred) if valor_cred else 0.0
    except ValueError:
        v_venda, v_pix, v_cred = 0.0, 0.0, 0.0

    foto_url_banco = None
    if 'foto_oficial' in request.files:
        arquivo = request.files['foto_oficial']
        if arquivo and arquivo.filename != '':
            nome_seguro = secure_filename(arquivo.filename)
            caminho_salvamento = os.path.join(DIRETORIO_CATALOGO, nome_seguro)
            arquivo.save(caminho_salvamento)
            foto_url_banco = f"/static/images/catalogo/{nome_seguro}"

    sucesso = admin_engine.salvar_produto_catalogo(
        produto_id, nome, categoria, plataforma, v_venda, v_pix, v_cred, int(ativo), foto_url_banco
    )
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'sucesso': sucesso,
            'mensagem': 'Produto salvo com sucesso!' if sucesso else 'Erro ao salvar o produto.'
        })

    flash('Produto salvo com sucesso!' if sucesso else 'Erro ao salvar produto.', 'success' if sucesso else 'error')
    return redirect(url_for('listar_catalogo'))

# --- ROTAS DE DADOS CORPORATIVOS ---
@app.route('/dados_empresa')
def dados_empresa():
    if session.get('admin_nivel') != 'Administrador':
        flash('Acesso restrito a Administradores.', 'error')
        return redirect(url_for('dashboard'))
        
    empresa = admin_engine.obter_dados_empresa()
    return render_template('configuracoes/empresa.html', empresa=empresa)

@app.route('/dados_empresa/salvar', methods=['POST'])
def salvar_empresa():
    if session.get('admin_nivel') != 'Administrador':
        return jsonify({'success': False, 'error': 'Acesso restrito a Administradores.'}), 403
        
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
        
    sucesso = admin_engine.salvar_dados_empresa(data)
    
    if sucesso:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Erro ao salvar os dados da empresa no banco de dados.'})

# --- ROTAS DE CATEGORIAS (CRUD) ---
@app.route('/categorias')
@requer_permissao('catalogo', 'read')
def listar_categorias():
    lista_categorias = admin_engine.get_categorias()
    return render_template('configuracoes/categorias.html', lista_categorias=lista_categorias)

@app.route('/categorias/salvar', methods=['POST'])
@requer_permissao('catalogo', 'update')
def salvar_categoria():
    cat_id = request.form.get('id')
    nome = request.form.get('nome')
    ativo = request.form.get('ativo')
    
    cat_id = int(cat_id) if cat_id and cat_id.isdigit() else None
    ativo_int = 1 if ativo else 0
    
    sucesso = admin_engine.upsert_categoria(cat_id, nome, ativo_int)
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'sucesso': sucesso,
            'mensagem': 'Categoria salva com sucesso!' if sucesso else 'Erro ao salvar a categoria.'
        })
    
    if sucesso:
        flash('Categoria salva com sucesso!', 'success')
    else:
        flash('Erro ao salvar a categoria. Tente novamente.', 'error')
        
    return redirect(url_for('listar_categorias'))

# --- ROTAS DE CANAIS DE AQUISIÇÃO (CRUD) ---
@app.route('/canais')
@requer_permissao('catalogo', 'read')
def listar_canais():
    lista_canais = admin_engine.get_canais()
    return render_template('configuracoes/canais.html', lista_canais=lista_canais)

@app.route('/canais/salvar', methods=['POST'])
@requer_permissao('catalogo', 'update')
def salvar_canal():
    canal_id = request.form.get('id')
    nome = request.form.get('nome')
    ativo = request.form.get('ativo')
    
    canal_id = int(canal_id) if canal_id and canal_id.isdigit() else None
    ativo_int = 1 if ativo else 0
    
    sucesso = admin_engine.upsert_canal(canal_id, nome, ativo_int)
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'sucesso': sucesso,
            'mensagem': 'Canal de aquisição salvo com sucesso!' if sucesso else 'Erro ao salvar o canal de aquisição.'
        })
    
    if sucesso:
        flash('Canal de aquisição salvo com sucesso!', 'success')
    else:
        flash('Erro ao salvar o canal de aquisição. Tente novamente.', 'error')
        
    return redirect(url_for('listar_canais'))

# --- ROTAS DE STATUS DE PROTOCOLOS (CRUD) ---
@app.route('/status')
@requer_permissao('protocolos', 'read')
def listar_status():
    lista_status = admin_engine.obter_todos_status()
    return render_template('configuracoes/status.html', lista_status=lista_status)

@app.route('/status/salvar', methods=['POST'])
@requer_permissao('protocolos', 'update')
def salvar_status():
    status_id = request.form.get('id')
    nome_exibicao = request.form.get('nome_exibicao')
    cor_badge = request.form.get('cor_badge')
    ativo = request.form.get('ativo')
    
    status_id = int(status_id) if status_id and status_id.isdigit() else None
    ativo_int = 1 if ativo else 0
    
    sucesso = admin_engine.upsert_status(status_id, nome_exibicao, cor_badge, ativo_int)
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'sucesso': sucesso,
            'mensagem': 'Status do protocolo salvo com sucesso!' if sucesso else 'Erro ao salvar o status.'
        })
    
    if sucesso:
        flash('Status do protocolo salvo com sucesso!', 'success')
    else:
        flash('Erro ao salvar o status. Tente novamente.', 'error')
        
    return redirect(url_for('listar_status'))

# --- ROTAS DE PERGUNTAS DE CONSERVAÇÃO (CRUD COM FILTRO OPCIONAL) ---
@app.route('/perguntas')
@app.route('/perguntas/<int:categoria_id>')
@requer_permissao('catalogo', 'read')
def listar_perguntas(categoria_id=None):
    todas_perguntas = admin_engine.obter_todas_perguntas()
    
    # Se um ID de categoria foi passado, filtramos as perguntas em Python
    if categoria_id:
        lista_perguntas = [p for p in todas_perguntas if p['categoria_id'] == categoria_id]
    else:
        lista_perguntas = [] # Mantém vazio se não houver categoria selecionada
        
    lista_categorias = admin_engine.get_categorias() 
    categoria_ativa = next((c for c in lista_categorias if c['id'] == categoria_id), None)
    
    return render_template('configuracoes/perguntas.html', 
                           lista_perguntas=lista_perguntas, 
                           lista_categorias=lista_categorias,
                           categoria_selecionada=categoria_id,
                           categoria_ativa=categoria_ativa)

@app.route('/perguntas/salvar', methods=['POST'])
@requer_permissao('catalogo', 'update')
def salvar_pergunta():
    perg_id = request.form.get('id')
    texto = request.form.get('texto_pergunta')
    categoria_id = request.form.get('categoria_id')
    tipo = request.form.get('tipo_resposta')
    impacto = request.form.get('impacto_valor')
    
    perg_id = int(perg_id) if perg_id and perg_id.isdigit() else None
    categoria_id = int(categoria_id) if categoria_id and categoria_id.isdigit() else None
    
    try:
        impacto_float = float(impacto) if impacto else 0.0
    except ValueError:
        impacto_float = 0.0
        
    sucesso = admin_engine.upsert_pergunta(perg_id, texto, categoria_id, tipo, impacto_float)
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'sucesso': sucesso,
            'mensagem': 'Pergunta salva com sucesso!' if sucesso else 'Erro ao salvar a pergunta.'
        })
        
    return redirect(url_for('listar_perguntas', categoria_id=categoria_id))

# --- ROTAS DE OPÇÕES DE ESTADO (CRUD) ---
@app.route('/opcoes_estado')
@app.route('/opcoes_estado/<int:categoria_id>')
@requer_permissao('catalogo', 'read')
def listar_opcoes_estado(categoria_id=None):
    lista_opcoes = admin_engine.obter_opcoes_estado(categoria_id) if categoria_id else []
    lista_categorias = admin_engine.get_categorias()
    categoria_ativa = next((c for c in lista_categorias if c['id'] == categoria_id), None)
    
    return render_template('configuracoes/opcoes_estado.html', 
                           lista_opcoes=lista_opcoes,
                           categoria_selecionada=categoria_id,
                           categoria_ativa=categoria_ativa)

@app.route('/opcoes_estado/salvar', methods=['POST'])
@requer_permissao('catalogo', 'update')
def salvar_opcao_estado():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
        
    op_id = data.get('id')
    cat_id = data.get('categoria_id')
    descricao = data.get('descricao')
    dep = data.get('fator_depreciacao')
    extra = data.get('valor_fixo_extra')
    
    op_id = int(op_id) if op_id and str(op_id).isdigit() else None
    
    try:
        dep_float = float(dep) if dep else 0.0
        extra_float = float(extra) if extra else 0.0
    except ValueError:
        dep_float, extra_float = 0.0, 0.0
        
    try:
        sucesso = admin_engine.upsert_opcao_estado(op_id, cat_id, descricao, dep_float, extra_float)
        
        if sucesso:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Falha na gravação no banco de dados.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --- ROTAS DE USUÁRIOS ADMIN (CRUD) ---
@app.route('/usuarios')
@requer_permissao('catalogo', 'read')
def listar_usuarios():
    # Bloqueio em Nível de Rota para garantir que apenas o Administrador veja a lista
    if session.get('admin_nivel') != 'Administrador':
        flash('Acesso restrito a Administradores.', 'error')
        return redirect(url_for('dashboard'))
        
    lista_usuarios = admin_engine.obter_todos_usuarios()
    return render_template('configuracoes/usuarios.html', lista_usuarios=lista_usuarios)

@app.route('/usuarios/salvar', methods=['POST'])
@requer_permissao('catalogo', 'update')
def salvar_usuario():
    # Bloqueio em Nível de Rota para garantir que apenas o Administrador execute alterações
    if session.get('admin_nivel') != 'Administrador':
        return jsonify({'success': False, 'error': 'Acesso restrito a Administradores.'}), 403
        
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
        
    usr_id = data.get('id')
    nivel_acesso = data.get('nivel_acesso')
    ativo = data.get('ativo')
    
    usr_id = int(usr_id) if usr_id and str(usr_id).isdigit() else None
    ativo_int = 1 if ativo in [1, '1', True, 'True', 'true'] else 0
    
    sucesso = admin_engine.atualizar_permissoes_usuario(usr_id, nivel_acesso, ativo_int)
    
    if sucesso:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Erro ao atualizar as permissões no banco de dados.'})

# --- ROTAS DE REGIÕES DE ATENDIMENTO (CRUD) ---
@app.route('/regioes')
@requer_permissao('regioes', 'read')
def listar_regioes():
    lista_regioes = admin_engine.obter_todas_regioes()
    return render_template('configuracoes/regioes.html', regioes=lista_regioes)

@app.route('/regioes/salvar', methods=['POST'])
@requer_permissao('regioes', 'update')
def salvar_regiao():
    regiao_id = request.form.get('id')
    cidade = request.form.get('cidade')
    estado_uf = request.form.get('estado_uf')
    multiplicador_preco = request.form.get('multiplicador_preco')
    ativo = request.form.get('ativo')
    regiao_id = int(regiao_id) if regiao_id and regiao_id.isdigit() else None
    
    sucesso = admin_engine.salvar_regiao(regiao_id, cidade, estado_uf, float(multiplicador_preco), int(ativo))
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'sucesso': sucesso, 
            'mensagem': 'Região salva com sucesso!' if sucesso else 'Erro ao salvar a região no banco de dados.'
        })

    flash('Região salva com sucesso!' if sucesso else 'Erro ao salvar.', 'success' if sucesso else 'error')
    return redirect(url_for('listar_regioes'))

@app.route('/api/buscar_cidades')
@requer_permissao('regioes', 'read')
def api_buscar_cidades():
    termo = request.args.get('q', '')
    if not termo or len(termo) < 3:
        return jsonify([])

    try:
        req = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/municipios", timeout=5)
        if req.status_code != 200:
             return jsonify([])
        dados = req.json()
    except: 
        return jsonify([])
        
    cidades_filtradas = []
    
    if dados:
        for m in dados:
            nome_cidade = m.get('nome', '')
            if termo.lower() in nome_cidade.lower():
                micro = m.get('microrregiao') or {}
                meso = micro.get('mesorregiao') or {}
                uf_obj = meso.get('UF') or {}
                uf = uf_obj.get('sigla', '??')
                
                cidades_filtradas.append({'cidade': nome_cidade, 'uf': uf})
                if len(cidades_filtradas) >= 8:
                    break

    return jsonify(cidades_filtradas)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/uploads/pericia/<path:filename>')
def servir_midia_externa(filename):
    diretorio_fotos = os.getenv("DIRETORIO_UPLOADS_PERICIA")
    return send_from_directory(diretorio_fotos, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=(os.getenv("FLASK_DEBUG") == "1"), port=int(os.getenv("PORTA_FLASK", 5002)))