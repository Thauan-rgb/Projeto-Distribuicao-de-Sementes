from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import hashlib
import jwt
from datetime import datetime, timedelta
import os

# =========================================================================
# CONFIGURAÇÕES E INICIALIZAÇÃO
# =========================================================================

app = Flask(__name__)
CORS(app)

# Configurações do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Th@203157',
    'database': 'semeia_db'
}

# Chave secreta para JWT
app.config['SECRET_KEY'] = 'sua_chave_secreta_muito_segura_aqui'

# =========================================================================
# FUNÇÕES AUXILIARES
# =========================================================================

def create_connection():
    """Cria conexão com o banco de dados"""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"❌ Erro ao conectar com MySQL: {e}")
        return None

def hash_password(password):
    """Gera hash da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

# =========================================================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# =========================================================================

def init_database():
    """Inicializa o banco de dados e cria tabelas se não existirem"""
    connection = create_connection()
    if not connection:
        print("❌ Não foi possível conectar ao banco de dados")
        return
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # --- CRIAÇÃO DE TABELAS ---
        
        # 1. Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                senha_hash VARCHAR(255) NOT NULL,
                tipo_usuario ENUM('gerente', 'cooperativa', 'armazem', 'agente') NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # 2. Tabela de remessas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS remessas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                status ENUM('Disponível', 'Em trânsito', 'Reservado') NOT NULL,
                tipo_semente VARCHAR(100) NOT NULL,
                numero_lote VARCHAR(50) UNIQUE NOT NULL,
                data_entrada DATE NOT NULL,
                quantidade_kg DECIMAL(10,2) NOT NULL,
                armazem_vinculado VARCHAR(100) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                criado_por VARCHAR(255),
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # 3. Tabela de entregas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entregas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo VARCHAR(50) UNIQUE NOT NULL,
                destino VARCHAR(255) NOT NULL,
                motorista VARCHAR(255) NOT NULL,
                status ENUM('planejada', 'andamento', 'concluida', 'atrasada') NOT NULL,
                data_prevista DATE NOT NULL,
                numero_lote VARCHAR(50) NOT NULL,
                observacoes TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # 4. Tabela de notificações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notificacoes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                mensagem TEXT NOT NULL,
                tipo ENUM('info', 'success', 'warning', 'alert') DEFAULT 'info',
                lida BOOLEAN DEFAULT FALSE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # 5. Tabela de alertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alertas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tipo_semente VARCHAR(100) NOT NULL,
                localizacao VARCHAR(255) NOT NULL,
                nivel ENUM('grave', 'aviso', 'ok') DEFAULT 'aviso',
                mensagem TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # 6. Tabela de municípios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS municipios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(100) UNIQUE NOT NULL,
                total_sementes_kg DECIMAL(12,2) DEFAULT 0,
                total_agricultores INT DEFAULT 0,
                regiao ENUM('Metropolitana', 'Agreste', 'Sertão', 'Zona da Mata') DEFAULT 'Agreste',
                data_ultima_entrega DATE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # 7. Tabela de configurações do sistema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes_sistema (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chave VARCHAR(255) UNIQUE NOT NULL,
                valor TEXT NOT NULL,
                descricao TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # --- INSERÇÃO DE DADOS PADRÃO ---
        
        # 1. Notificações de exemplo
        cursor.execute("SELECT COUNT(*) FROM notificacoes")
        if cursor.fetchone()[0] == 0:
            notificacoes_exemplo = [
                ('Lote 002 entregue com sucesso!', 'Entrega concluída para o agricultor João Silva em Garanhuns', 'success'),
                ('Nova solicitação de sementes aprovada', 'Solicitação #2024-015 aprovada para distribuição', 'info'),
                ('Baixo estoque de Feijão Carioca', 'Estoque abaixo do nível mínimo no armazém central', 'warning'),
                ('Falha na entrega do lote 005', 'Endereço incorreto - necessário reagendamento', 'alert'),
                ('Nova remessa recebida', 'Remessa de milho registrada no sistema', 'success')
            ]
            for titulo, mensagem, tipo in notificacoes_exemplo:
                cursor.execute('INSERT INTO notificacoes (titulo, mensagem, tipo) VALUES (%s, %s, %s)', 
                             (titulo, mensagem, tipo))
            print("✅ Notificações de exemplo inseridas!")
        
        # 2. Alertas de exemplo
        cursor.execute("SELECT COUNT(*) FROM alertas")
        if cursor.fetchone()[0] == 0:
            alertas_exemplo = [
                ('Mandioca', 'Caruaru', 'grave', 'Falta grave, necessário reabastecimento.'),
                ('Feijão', 'Garanhuns', 'grave', 'Esgotado. Solicitar pedido de urgência.'),
                ('Abóbora', 'Vitória de Santo Antão', 'aviso', 'Nível baixo.'),
                ('Milho', 'Unidade de Petrolina', 'aviso', 'Nível mínimo.'),
                ('Arroz', 'Serra Talhada', 'ok', 'Pronto para distribuição.'),
                ('Inhame', 'Pesqueira', 'ok', 'Estoque satisfatório. Iniciar processo de embalagem.')
            ]
            for tipo, local, nivel, msg in alertas_exemplo:
                cursor.execute('INSERT INTO alertas (tipo_semente, localizacao, nivel, mensagem) VALUES (%s, %s, %s, %s)', 
                             (tipo, local, nivel, msg))
            print("✅ Alertas de exemplo inseridos!")
        
        # 3. Usuários Padrão
        usuarios_padrao = [
            ('gerente@ipa.gov.br', 'gerente123', 'gerente'),
            ('cooperativa@ipa.gov.br', 'cooperativa123', 'cooperativa'),
            ('armazem@ipa.gov.br', 'armazem123', 'armazem'),
            ('agente@ipa.gov.br', 'agente123', 'agente')
        ]
        
        for email, senha, tipo in usuarios_padrao:
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if not cursor.fetchone():
                senha_hash = hashlib.sha256(senha.encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO usuarios (email, senha_hash, tipo_usuario) VALUES (%s, %s, %s)",
                    (email, senha_hash, tipo)
                )
                print(f"✅ Usuário {email} criado com sucesso!")
        
        # 4. Municípios de Exemplo
        cursor.execute("SELECT COUNT(*) FROM municipios")
        count_result = cursor.fetchone()
        municipios_count = count_result[0] if count_result else 0
        
        if municipios_count == 0:
            municipios_exemplo = [
                ('Garanhuns', 15200, 152, 'Agreste', '2024-12-01'),
                ('Caruaru', 12500, 110, 'Agreste', '2024-12-01'),
                ('Petrolina', 9800, 95, 'Sertão', '2024-12-01'),
                ('Serra Talhada', 7100, 78, 'Sertão', '2024-12-01'),
                ('Recife', 5000, 45, 'Metropolitana', '2024-11-28'),
                ('Vitória de Santo Antão', 4200, 52, 'Zona da Mata', '2024-11-25'),
                ('Arcoverde', 3800, 41, 'Sertão', '2024-11-20'),
                ('Belo Jardim', 3200, 38, 'Agreste', '2024-11-18')
            ]
            for nome, sementes, agricultores, regiao, data_entrega in municipios_exemplo:
                try:
                    cursor.execute('''
                        INSERT INTO municipios (nome, total_sementes_kg, total_agricultores, regiao, data_ultima_entrega) 
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (nome, sementes, agricultores, regiao, data_entrega))
                    print(f"✅ Município {nome} inserido")
                except Error as e:
                    print(f"⚠️  Município {nome} já existe ou erro: {e}")
                    continue
            print("✅ Municípios de exemplo inseridos!")
        else:
            print(f"✅ Tabela municipios já possui {municipios_count} registros")
        
        # 5. Configurações Padrão
        configuracoes_padrao = [
            ('nome_instituicao', 'IPA - Instituto Agronômico de Pernambuco', 'Nome completo da instituição'),
            ('email_institucional', 'contato@ipa.gov.br', 'Email principal da instituição'),
            ('telefone_contato', '(81) 99999-9999', 'Telefone para contato'),
            ('endereco_instituicao', 'Recife, PE', 'Endereço da instituição'),
            ('itens_por_pagina', '10', 'Número de itens exibidos por página'),
            ('idioma_padrao', 'pt-br', 'Idioma padrão do sistema'),
            ('estoque_minimo_alertas', '100', 'Estoque mínimo para gerar alertas (kg)'),
            ('dias_alerta_vencimento', '30', 'Dias para alerta de vencimento'),
            ('email_alertas_estoque', 'estoque@ipa.gov.br', 'Email para receber alertas de estoque'),
            ('backup_automatico', 'true', 'Habilitar backup automático'),
            ('modo_manutencao', 'false', 'Modo de manutenção do sistema')
        ]
        
        for chave, valor, descricao in configuracoes_padrao:
            cursor.execute('''
                INSERT IGNORE INTO configuracoes_sistema (chave, valor, descricao) 
                VALUES (%s, %s, %s)
            ''', (chave, valor, descricao))
        print("✅ Tabela de configurações do sistema inicializada!")
        
        connection.commit()
        print("✅ Inicialização completa do banco de dados!")
        
    except Error as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS DE AUTENTICAÇÃO
# =========================================================================

@app.route('/api/login', methods=['POST'])
def login():
    """Endpoint para login"""
    print("=== DEBUG: Endpoint /api/login chamado ===")
    
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Dados recebidos: {data}")
        
        email = data.get('email', '').lower().strip()
        senha = data.get('senha', '').strip()
        
        if not email or not senha:
            return jsonify({'success': False, 'message': 'Email e senha são obrigatórios'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor - não foi possível conectar ao banco'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, email, senha_hash, tipo_usuario FROM usuarios WHERE email = %s AND ativo = TRUE",
            (email,)
        )
        usuario = cursor.fetchone()
        
        print(f"DEBUG: Usuário encontrado no banco: {usuario}")
        
        if usuario and usuario['senha_hash'] == hash_password(senha):
            token = jwt.encode({
                'user_id': usuario['id'],
                'email': usuario['email'],
                'tipo': usuario['tipo_usuario'],
                'exp': datetime.utcnow() + timedelta(hours=1)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            redirect_map = {
                'gerente': 'Gestor/dashboard_gerente.html',
                'cooperativa': 'Cooperativa/dashboard_cooperativa.html',
                'armazem': 'Armazem/dashboard_operador.html',
                'agente': 'Agente/dashboard_agente.html'
            }
            
            redirect_url = redirect_map.get(usuario['tipo_usuario'])
            
            print(f"DEBUG: Login bem-sucedido! Redirecionando para: {redirect_url}")
            
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'tipo_usuario': usuario['tipo_usuario'],
                'token': token,
                'redirect': redirect_url
            })
        else:
            print("DEBUG: Credenciais inválidas")
            return jsonify({'success': False, 'message': 'Email ou senha incorretos'}), 401
            
    except Error as e:
        print(f"❌ Erro no login (MySQL): {e}")
        return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
    except Exception as e:
        print(f"❌ Erro no login (Geral): {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/criar-senha', methods=['POST'])
def criar_senha():
    """Endpoint para criar nova senha"""
    print("=== DEBUG: Endpoint /api/criar-senha chamado ===")
    
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Dados recebidos: {data}")
        
        email = data.get('email', '').lower().strip()
        nova_senha = data.get('nova_senha', '').strip()
        confirmar_senha = data.get('confirmar_senha', '').strip()
        
        if not email or not nova_senha or not confirmar_senha:
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'}), 400
        
        if nova_senha != confirmar_senha:
            return jsonify({'success': False, 'message': 'As senhas não coincidem'}), 400
        
        if len(nova_senha) < 6:
            return jsonify({'success': False, 'message': 'A senha deve ter pelo menos 6 caracteres'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Este email já está cadastrado'}), 400
        
        if 'gerente' in email:
            tipo = 'gerente'
        elif 'cooperativa' in email:
            tipo = 'cooperativa'
        elif 'armazem' in email:
            tipo = 'armazem'
        elif 'agente' in email:
            tipo = 'agente'
        else:
            tipo = 'agente'
        
        senha_hash = hash_password(nova_senha)
        cursor.execute(
            "INSERT INTO usuarios (email, senha_hash, tipo_usuario) VALUES (%s, %s, %s)",
            (email, senha_hash, tipo)
        )
        
        connection.commit()
        print(f"✅ Novo usuário criado: {email} (tipo: {tipo})")
        
        return jsonify({'success': True, 'message': 'Senha criada com sucesso! Você já pode fazer login.'})
        
    except Error as e:
        print(f"❌ Erro ao criar senha (MySQL): {e}")
        return jsonify({'success': False, 'message': 'Erro ao criar conta'}), 500
    except Exception as e:
        print(f"❌ Erro ao criar senha (Geral): {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS DE REMESSAS
# =========================================================================

@app.route('/api/adicionar-remessa', methods=['POST'])
def adicionar_remessa():
    """Endpoint para adicionar nova remessa"""
    print("=== DEBUG: Endpoint /api/adicionar-remessa chamado ===")
    
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Dados recebidos: {data}")
        
        status = data.get('status', '').strip()
        tipo_semente = data.get('tipo_semente', '').strip()
        numero_lote = data.get('numero_lote', '').strip()
        data_entrada = data.get('data_entrada', '').strip()
        quantidade_kg = data.get('quantidade_kg', '').strip()
        armazem_vinculado = data.get('armazem_vinculado', '').strip()
        criado_por = data.get('criado_por', 'Sistema')
        
        if not all([status, tipo_semente, numero_lote, data_entrada, quantidade_kg, armazem_vinculado]):
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'}), 400
        
        try:
            quantidade_limpa = quantidade_kg.replace('kg', '').replace('Kg', '').replace('KG', '').strip()
            quantidade_kg_float = float(quantidade_limpa)
        except ValueError:
            return jsonify({'success': False, 'message': 'Quantidade deve ser um número válido'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM remessas WHERE numero_lote = %s", (numero_lote,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Número do lote já existe'}), 400
        
        cursor.execute('''
            INSERT INTO remessas 
            (status, tipo_semente, numero_lote, data_entrada, quantidade_kg, armazem_vinculado, criado_por) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (status, tipo_semente, numero_lote, data_entrada, quantidade_kg_float, armazem_vinculado, criado_por))
        
        connection.commit()
        print(f"✅ Nova remessa adicionada: {numero_lote} - {tipo_semente} - {quantidade_kg_float}kg")
        
        return jsonify({'success': True, 'message': 'Remessa adicionada com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao adicionar remessa (MySQL): {e}")
        return jsonify({'success': False, 'message': 'Erro ao salvar remessa'}), 500
    except Exception as e:
        print(f"❌ Erro geral ao adicionar remessa: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/listar-remessas', methods=['GET'])
def listar_remessas():
    """Endpoint para listar todas as remessas"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, status, tipo_semente, numero_lote, data_entrada, 
                    quantidade_kg, armazem_vinculado, data_criacao, criado_por
            FROM remessas 
            WHERE ativo = TRUE 
            ORDER BY data_criacao DESC
        ''')
        
        remessas = cursor.fetchall()
        
        for remessa in remessas:
            if remessa.get('data_entrada'):
                remessa['data_entrada'] = remessa['data_entrada'].strftime('%Y-%m-%d')
            if remessa.get('data_criacao'):
                remessa['data_criacao'] = remessa['data_criacao'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'remessas': remessas,
            'total': len(remessas)
        })
        
    except Error as e:
        print(f"❌ Erro ao listar remessas: {e}")
        return jsonify({'success': False, 'message': 'Erro ao buscar remessas'}), 500
    except Exception as e:
        print(f"❌ Erro geral ao listar remessas: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/editar-remessa/<int:id>', methods=['PUT'])
def editar_remessa(id):
    """Endpoint para editar uma remessa existente"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM remessas WHERE id = %s AND ativo = TRUE", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Remessa não encontrada'}), 404
        
        cursor.execute('''
            UPDATE remessas 
            SET status = %s, tipo_semente = %s, numero_lote = %s, 
                data_entrada = %s, quantidade_kg = %s, armazem_vinculado = %s
            WHERE id = %s
        ''', (
            data.get('status'),
            data.get('tipo_semente'), 
            data.get('numero_lote'),
            data.get('data_entrada'),
            data.get('quantidade_kg'),
            data.get('armazem_vinculado'),
            id
        ))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Remessa atualizada com sucesso!'})
        
    except Error as e:
        print(f"Erro ao editar remessa: {e}")
        return jsonify({'success': False, 'message': 'Erro ao atualizar remessa'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/deletar-remessa/<int:id>', methods=['DELETE'])
def deletar_remessa(id):
    """Endpoint para deletar uma remessa (soft delete)"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM remessas WHERE id = %s AND ativo = TRUE", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Remessa não encontrada'}), 404
        
        cursor.execute("UPDATE remessas SET ativo = FALSE WHERE id = %s", (id,))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Remessa excluída com sucesso!'})
        
    except Error as e:
        print(f"Erro ao deletar remessa: {e}")
        return jsonify({'success': False, 'message': 'Erro ao excluir remessa'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS DE USUÁRIOS
# =========================================================================

@app.route('/api/listar-usuarios', methods=['GET'])
def listar_usuarios():
    """Endpoint para listar todos os usuários"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, email, tipo_usuario, data_criacao, ativo
            FROM usuarios 
            WHERE ativo = TRUE 
            ORDER BY data_criacao DESC
        ''')
        
        usuarios = cursor.fetchall()
        
        for usuario in usuarios:
            if usuario.get('data_criacao'):
                usuario['data_criacao'] = usuario['data_criacao'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'usuarios': usuarios,
            'total': len(usuarios)
        })
        
    except Error as e:
        print(f"❌ Erro ao listar usuários: {e}")
        return jsonify({'success': False, 'message': 'Erro ao buscar usuários'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/adicionar-usuario', methods=['POST'])
def adicionar_usuario():
    """Endpoint para adicionar novo usuário"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Dados recebidos para adicionar usuário: {data}")
        
        email = data.get('email', '').lower().strip()
        senha = data.get('senha', '').strip()
        tipo_usuario = data.get('tipo_usuario', '').strip()
        
        if not all([email, senha, tipo_usuario]):
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'}), 400
        
        if len(senha) < 6:
            return jsonify({'success': False, 'message': 'A senha deve ter pelo menos 6 caracteres'}), 400
        
        if tipo_usuario not in ['gerente', 'cooperativa', 'armazem', 'agente']:
            return jsonify({'success': False, 'message': 'Tipo de usuário inválido'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Este email já está cadastrado'}), 400
        
        senha_hash = hash_password(senha)
        cursor.execute(
            "INSERT INTO usuarios (email, senha_hash, tipo_usuario) VALUES (%s, %s, %s)",
            (email, senha_hash, tipo_usuario)
        )
        
        connection.commit()
        print(f"✅ Novo usuário criado: {email} (tipo: {tipo_usuario})")
        return jsonify({'success': True, 'message': 'Usuário criado com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao adicionar usuário: {e}")
        return jsonify({'success': False, 'message': 'Erro ao criar usuário'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/editar-usuario/<int:id>', methods=['PUT'])
def editar_usuario(id):
    """Endpoint para editar um usuário existente"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Dados recebidos para editar usuário {id}: {data}")
        
        email = data.get('email', '').lower().strip()
        tipo_usuario = data.get('tipo_usuario', '').strip()
        nova_senha = data.get('nova_senha', '').strip()
        
        if not all([email, tipo_usuario]):
            return jsonify({'success': False, 'message': 'Email e tipo são obrigatórios'}), 400
        
        if tipo_usuario not in ['gerente', 'cooperativa', 'armazem', 'agente']:
            return jsonify({'success': False, 'message': 'Tipo de usuário inválido'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM usuarios WHERE id = %s AND ativo = TRUE", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        cursor.execute("SELECT id FROM usuarios WHERE email = %s AND id != %s", (email, id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Este email já está em uso'}), 400
        
        if nova_senha:
            if len(nova_senha) < 6:
                return jsonify({'success': False, 'message': 'A senha deve ter pelo menos 6 caracteres'}), 400
            senha_hash = hash_password(nova_senha)
            cursor.execute('''
                UPDATE usuarios 
                SET email = %s, tipo_usuario = %s, senha_hash = %s
                WHERE id = %s
            ''', (email, tipo_usuario, senha_hash, id))
        else:
            cursor.execute('''
                UPDATE usuarios 
                SET email = %s, tipo_usuario = %s
                WHERE id = %s
            ''', (email, tipo_usuario, id))
        
        connection.commit()
        print(f"✅ Usuário {id} atualizado: {email} (tipo: {tipo_usuario})")
        return jsonify({'success': True, 'message': 'Usuário atualizado com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao editar usuário: {e}")
        return jsonify({'success': False, 'message': 'Erro ao atualizar usuário'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/deletar-usuario/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    """Endpoint para deletar um usuário (soft delete)"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id, email FROM usuarios WHERE id = %s AND ativo = TRUE", (id,))
        usuario = cursor.fetchone()
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        cursor.execute("UPDATE usuarios SET ativo = FALSE WHERE id = %s", (id,))
        
        connection.commit()
        print(f"✅ Usuário {id} deletado (soft delete)")
        return jsonify({'success': True, 'message': 'Usuário excluído com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao deletar usuário: {e}")
        return jsonify({'success': False, 'message': 'Erro ao excluir usuário'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS DE ENTREGAS
# =========================================================================

@app.route('/api/listar-entregas', methods=['GET'])
def listar_entregas():
    """Endpoint para listar todas as entregas"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, codigo, destino, motorista, status, data_prevista, 
                    numero_lote, observacoes, data_criacao
            FROM entregas 
            WHERE ativo = TRUE 
            ORDER BY data_criacao DESC
        ''')
        
        entregas = cursor.fetchall()
        
        for entrega in entregas:
            if entrega.get('data_prevista'):
                entrega['data_prevista'] = entrega['data_prevista'].strftime('%Y-%m-%d')
            if entrega.get('data_criacao'):
                entrega['data_criacao'] = entrega['data_criacao'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'entregas': entregas,
            'total': len(entregas)
        })
        
    except Error as e:
        print(f"❌ Erro ao listar entregas: {e}")
        return jsonify({'success': False, 'message': 'Erro ao buscar entregas'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/adicionar-entrega', methods=['POST'])
def adicionar_entrega():
    """Endpoint para adicionar nova entrega"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Dados recebidos para adicionar entrega: {data}")
        
        codigo = data.get('codigo', '').strip()
        destino = data.get('destino', '').strip()
        motorista = data.get('motorista', '').strip()
        status = data.get('status', '').strip()
        data_prevista = data.get('data_prevista', '').strip()
        numero_lote = data.get('numero_lote', '').strip()
        observacoes = data.get('observacoes', '').strip()
        
        if not all([codigo, destino, motorista, status, data_prevista, numero_lote]):
            return jsonify({'success': False, 'message': 'Todos os campos obrigatórios devem ser preenchidos'}), 400
        
        if status not in ['planejada', 'andamento', 'concluida', 'atrasada']:
            return jsonify({'success': False, 'message': 'Status inválido'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM entregas WHERE codigo = %s", (codigo,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Código da entrega já existe'}), 400
        
        cursor.execute('''
            INSERT INTO entregas 
            (codigo, destino, motorista, status, data_prevista, numero_lote, observacoes) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (codigo, destino, motorista, status, data_prevista, numero_lote, observacoes))
        
        connection.commit()
        print(f"✅ Nova entrega adicionada: {codigo} - {destino}")
        return jsonify({'success': True, 'message': 'Entrega cadastrada com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao adicionar entrega: {e}")
        return jsonify({'success': False, 'message': 'Erro ao salvar entrega'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/editar-entrega/<int:id>', methods=['PUT'])
def editar_entrega(id):
    """Endpoint para editar uma entrega existente"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Dados recebidos para editar entrega {id}: {data}")
        
        codigo = data.get('codigo', '').strip()
        destino = data.get('destino', '').strip()
        motorista = data.get('motorista', '').strip()
        status = data.get('status', '').strip()
        data_prevista = data.get('data_prevista', '').strip()
        numero_lote = data.get('numero_lote', '').strip()
        observacoes = data.get('observacoes', '').strip()
        
        if not all([codigo, destino, motorista, status, data_prevista, numero_lote]):
            return jsonify({'success': False, 'message': 'Todos os campos obrigatórios devem ser preenchidos'}), 400
        
        if status not in ['planejada', 'andamento', 'concluida', 'atrasada']:
            return jsonify({'success': False, 'message': 'Status inválido'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM entregas WHERE id = %s AND ativo = TRUE", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Entrega não encontrada'}), 404
        
        cursor.execute("SELECT id FROM entregas WHERE codigo = %s AND id != %s", (codigo, id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Código da entrega já existe'}), 400
        
        cursor.execute('''
            UPDATE entregas 
            SET codigo = %s, destino = %s, motorista = %s, status = %s, 
                data_prevista = %s, numero_lote = %s, observacoes = %s
            WHERE id = %s
        ''', (codigo, destino, motorista, status, data_prevista, numero_lote, observacoes, id))
        
        connection.commit()
        print(f"✅ Entrega {id} atualizada: {codigo}")
        return jsonify({'success': True, 'message': 'Entrega atualizada com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao editar entrega: {e}")
        return jsonify({'success': False, 'message': 'Erro ao atualizar entrega'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/deletar-entrega/<int:id>', methods=['DELETE'])
def deletar_entrega(id):
    """Endpoint para deletar uma entrega (soft delete)"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT id, codigo FROM entregas WHERE id = %s AND ativo = TRUE", (id,))
        entrega = cursor.fetchone()
        if not entrega:
            return jsonify({'success': False, 'message': 'Entrega não encontrada'}), 404
        
        cursor.execute("UPDATE entregas SET ativo = FALSE WHERE id = %s", (id,))
        
        connection.commit()
        print(f"✅ Entrega {id} deletada: {entrega['codigo']}")
        return jsonify({'success': True, 'message': 'Entrega excluída com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao deletar entrega: {e}")
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'message': 'Erro ao excluir entrega'}), 500
    except Exception as e:
        print(f"❌ Erro geral ao deletar entrega: {e}")
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/estatisticas-entregas', methods=['GET'])
def estatisticas_entregas():
    """Endpoint para obter estatísticas das entregas"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT status, COUNT(*) as quantidade 
            FROM entregas 
            WHERE ativo = TRUE 
            GROUP BY status
        ''')
        
        estatisticas = cursor.fetchall()
        
        resultado = {
            'planejada': 0,
            'andamento': 0,
            'concluida': 0,
            'atrasada': 0,
            'total': 0
        }
        
        for estatistica in estatisticas:
            resultado[estatistica['status']] = estatistica['quantidade']
            resultado['total'] += estatistica['quantidade']
        
        return jsonify({
            'success': True,
            'estatisticas': resultado
        })
        
    except Error as e:
        print(f"❌ Erro ao buscar estatísticas: {e}")
        return jsonify({'success': False, 'message': 'Erro ao buscar estatísticas'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS DE NOTIFICAÇÕES
# =========================================================================

@app.route('/api/notificacoes', methods=['GET'])
def listar_notificacoes():
    """Endpoint para listar todas as notificações"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, titulo, mensagem, tipo, lida, data_criacao
            FROM notificacoes 
            WHERE ativo = TRUE 
            ORDER BY data_criacao DESC
        ''')
        
        notificacoes = cursor.fetchall()
        
        for notificacao in notificacoes:
            if notificacao.get('data_criacao'):
                notificacao['data_criacao'] = notificacao['data_criacao'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'notificacoes': notificacoes,
            'total': len(notificacoes)
        })
        
    except Error as e:
        print(f"❌ Erro ao listar notificações: {e}")
        return jsonify({'success': False, 'message': 'Erro ao buscar notificações'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/notificacoes', methods=['POST'])
def criar_notificacao():
    """Endpoint para criar nova notificação"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        
        titulo = data.get('titulo', '').strip()
        mensagem = data.get('mensagem', '').strip()
        tipo = data.get('tipo', 'info').strip()
        
        if not titulo or not mensagem:
            return jsonify({'success': False, 'message': 'Título e mensagem são obrigatórios'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO notificacoes (titulo, mensagem, tipo) 
            VALUES (%s, %s, %s)
        ''', (titulo, mensagem, tipo))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Notificação criada com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao criar notificação: {e}")
        return jsonify({'success': False, 'message': 'Erro ao criar notificação'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/notificacoes/<int:id>/ler', methods=['PUT'])
def marcar_como_lida(id):
    """Endpoint para marcar notificação como lida"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE notificacoes SET lida = TRUE WHERE id = %s
        ''', (id,))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Notificação marcada como lida!'})
        
    except Error as e:
        print(f"❌ Erro ao marcar notificação como lida: {e}")
        return jsonify({'success': False, 'message': 'Erro ao atualizar notificação'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/notificacoes/<int:id>', methods=['DELETE'])
def deletar_notificacao(id):
    """Endpoint para deletar uma notificação"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE notificacoes SET ativo = FALSE WHERE id = %s
        ''', (id,))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Notificação excluída com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao deletar notificação: {e}")
        return jsonify({'success': False, 'message': 'Erro ao excluir notificação'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS DE ALERTAS
# =========================================================================

@app.route('/api/alertas', methods=['GET'])
def listar_alertas():
    """Endpoint para listar todos os alertas"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, tipo_semente, localizacao, nivel, mensagem, 
                   DATE_FORMAT(data_criacao, '%%Y-%%m-%%d %%H:%%i:%%s') as data_criacao
            FROM alertas 
            WHERE ativo = TRUE 
            ORDER BY data_criacao DESC
        ''')
        
        alertas = cursor.fetchall()
        
        print("DEBUG - Alertas encontrados:", alertas)
        
        return jsonify({
            'success': True,
            'alertas': alertas,
            'total': len(alertas)
        })
        
    except Error as e:
        print(f"❌ Erro ao listar alertas: {e}")
        return jsonify({'success': False, 'message': 'Erro ao buscar alertas'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/alertas', methods=['POST'])
def criar_alerta():
    """Endpoint para criar novo alerta"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Criando alerta - Dados recebidos: {data}")
        
        tipo_semente = data.get('tipo_semente', '').strip()
        localizacao = data.get('localizacao', '').strip()
        nivel = data.get('nivel', 'aviso').strip()
        mensagem = data.get('mensagem', '').strip()
        
        if not tipo_semente or not localizacao or not mensagem:
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'}), 400
        
        if nivel not in ['grave', 'aviso', 'ok']:
            return jsonify({'success': False, 'message': 'Nível de alerta inválido'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute('''
            INSERT INTO alertas (tipo_semente, localizacao, nivel, mensagem) 
            VALUES (%s, %s, %s, %s)
        ''', (tipo_semente, localizacao, nivel, mensagem))
        
        connection.commit()
        print(f"✅ Alerta criado: {tipo_semente} - {localizacao}")
        
        return jsonify({
            'success': True, 
            'message': 'Alerta criado com sucesso!'
        })
        
    except Error as e:
        print(f"❌ Erro MySQL ao criar alerta: {e}")
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'message': f'Erro no banco de dados: {str(e)}'}), 500
    except Exception as e:
        print(f"❌ Erro geral ao criar alerta: {e}")
        if connection and connection.is_connected():
            connection.rollback()
        return jsonify({'success': False, 'message': f'Erro interno do servidor: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route('/api/alertas/<int:id>', methods=['PUT'])
def editar_alerta(id):
    """Endpoint para editar um alerta existente"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Editando alerta {id}: {data}")
        
        tipo_semente = data.get('tipo_semente', '').strip()
        localizacao = data.get('localizacao', '').strip()
        nivel = data.get('nivel', 'aviso').strip()
        mensagem = data.get('mensagem', '').strip()
        
        if not tipo_semente or not localizacao or not mensagem:
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'}), 400
        
        if nivel not in ['grave', 'aviso', 'ok']:
            return jsonify({'success': False, 'message': 'Nível de alerta inválido'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM alertas WHERE id = %s AND ativo = TRUE", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Alerta não encontrado'}), 404
        
        cursor.execute('''
            UPDATE alertas 
            SET tipo_semente = %s, localizacao = %s, nivel = %s, mensagem = %s
            WHERE id = %s
        ''', (tipo_semente, localizacao, nivel, mensagem, id))
        
        connection.commit()
        print(f"✅ Alerta {id} atualizado com sucesso")
        return jsonify({'success': True, 'message': 'Alerta atualizado com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao editar alerta: {e}")
        return jsonify({'success': False, 'message': 'Erro ao atualizar alerta'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/alertas/<int:id>', methods=['DELETE'])
def deletar_alerta(id):
    """Endpoint para deletar um alerta"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM alertas WHERE id = %s AND ativo = TRUE", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Alerta não encontrado'}), 404
        
        cursor.execute('UPDATE alertas SET ativo = FALSE WHERE id = %s', (id,))
        
        connection.commit()
        print(f"✅ Alerta {id} deletado com sucesso")
        return jsonify({'success': True, 'message': 'Alerta excluído com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao deletar alerta: {e}")
        return jsonify({'success': False, 'message': 'Erro ao excluir alerta'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS DE CONFIGURAÇÕES DO SISTEMA
# =========================================================================

@app.route('/api/configuracoes', methods=['GET'])
def listar_configuracoes():
    """Endpoint para listar todas as configurações do sistema"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT chave, valor, descricao 
            FROM configuracoes_sistema 
            WHERE ativo = TRUE 
            ORDER BY chave
        ''')
        
        configuracoes = cursor.fetchall()
        
        config_dict = {item['chave']: item['valor'] for item in configuracoes}
        
        return jsonify({
            'success': True,
            'configuracoes': config_dict,
            'total': len(configuracoes)
        })
        
    except Error as e:
        print(f"❌ Erro ao listar configurações: {e}")
        return jsonify({'success': False, 'message': 'Erro ao buscar configurações'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/configuracoes/<string:chave>', methods=['GET'])
def obter_configuracao(chave):
    """Endpoint para obter uma configuração específica"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT chave, valor, descricao 
            FROM configuracoes_sistema 
            WHERE chave = %s AND ativo = TRUE
        ''', (chave,))
        
        configuracao = cursor.fetchone()
        
        if not configuracao:
            return jsonify({'success': False, 'message': 'Configuração não encontrada'}), 404
        
        return jsonify({
            'success': True,
            'configuracao': configuracao
        })
        
    except Error as e:
        print(f"❌ Erro ao buscar configuração: {e}")
        return jsonify({'success': False, 'message': 'Erro ao buscar configuração'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/configuracoes/informacoes-institucionais', methods=['PUT'])
def atualizar_informacoes_institucionais():
    """Endpoint para atualizar informações institucionais"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Atualizando informações institucionais: {data}")
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        configuracoes = [
            ('nome_instituicao', data.get('nome_instituicao')),
            ('email_institucional', data.get('email_institucional')),
            ('telefone_contato', data.get('telefone_contato')),
            ('endereco_instituicao', data.get('endereco_instituicao'))
        ]
        
        for chave, valor in configuracoes:
            if valor is not None:
                cursor.execute('''
                    UPDATE configuracoes_sistema 
                    SET valor = %s 
                    WHERE chave = %s
                ''', (valor, chave))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Informações institucionais salvas com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao atualizar informações institucionais: {e}")
        return jsonify({'success': False, 'message': 'Erro ao salvar informações'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/configuracoes/sistema', methods=['PUT'])
def atualizar_configuracoes_sistema():
    """Endpoint para atualizar configurações do sistema"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Atualizando configurações do sistema: {data}")
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        configuracoes = [
            ('itens_por_pagina', data.get('itens_por_pagina')),
            ('idioma_padrao', data.get('idioma_padrao')),
            ('modo_manutencao', 'true' if data.get('modo_manutencao') else 'false'),
            ('backup_automatico', 'true' if data.get('backup_automatico') else 'false')
        ]
        
        for chave, valor in configuracoes:
            if valor is not None:
                cursor.execute('''
                    UPDATE configuracoes_sistema 
                    SET valor = %s 
                    WHERE chave = %s
                ''', (valor, chave))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Configurações de sistema salvas com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao atualizar configurações do sistema: {e}")
        return jsonify({'success': False, 'message': 'Erro ao salvar configurações'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/configuracoes/estoque', methods=['PUT'])
def atualizar_configuracoes_estoque():
    """Endpoint para atualizar configurações de estoque"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Atualizando configurações de estoque: {data}")
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        configuracoes = [
            ('estoque_minimo_alertas', data.get('estoque_minimo_alertas')),
            ('dias_alerta_vencimento', data.get('dias_alerta_vencimento')),
            ('email_alertas_estoque', data.get('email_alertas_estoque'))
        ]
        
        for chave, valor in configuracoes:
            if valor is not None:
                cursor.execute('''
                    UPDATE configuracoes_sistema 
                    SET valor = %s 
                    WHERE chave = %s
                ''', (valor, chave))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Configurações de estoque salvas com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao atualizar configurações de estoque: {e}")
        return jsonify({'success': False, 'message': 'Erro ao salvar configurações'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/configuracoes', methods=['POST'])
def criar_configuracao():
    """Endpoint para criar nova configuração"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        
        chave = data.get('chave', '').strip()
        valor = data.get('valor', '').strip()
        descricao = data.get('descricao', '').strip()
        
        if not chave or not valor:
            return jsonify({'success': False, 'message': 'Chave e valor são obrigatórios'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM configuracoes_sistema WHERE chave = %s", (chave,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Configuração já existe'}), 400
        
        cursor.execute('''
            INSERT INTO configuracoes_sistema (chave, valor, descricao) 
            VALUES (%s, %s, %s)
        ''', (chave, valor, descricao))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Configuração criada com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao criar configuração: {e}")
        return jsonify({'success': False, 'message': 'Erro ao criar configuração'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/configuracoes/<string:chave>', methods=['DELETE'])
def deletar_configuracao(chave):
    """Endpoint para deletar uma configuração"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM configuracoes_sistema WHERE chave = %s AND ativo = TRUE", (chave,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Configuração não encontrada'}), 404
        
        cursor.execute("UPDATE configuracoes_sistema SET ativo = FALSE WHERE chave = %s", (chave,))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Configuração excluída com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao deletar configuração: {e}")
        return jsonify({'success': False, 'message': 'Erro ao excluir configuração'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS DE MUNICÍPIOS
# =========================================================================

@app.route('/api/municipios', methods=['GET'])
def listar_municipios():
    """Endpoint para listar todos os municípios - COM MAIS DEBUG"""
    connection = None
    cursor = None
    try:
        print("🔍 GET /api/municipios chamado")
        connection = create_connection()
        if not connection:
            print("❌ Falha na conexão com o banco")
            return jsonify({'success': False, 'message': 'Erro no servidor - não foi possível conectar ao banco'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT id, nome, total_sementes_kg, total_agricultores, regiao, 
                   data_ultima_entrega, data_criacao, ativo
            FROM municipios 
            WHERE ativo = TRUE 
            ORDER BY total_sementes_kg DESC
        ''')
        
        municipios = cursor.fetchall()
        print(f"✅ {len(municipios)} municípios encontrados")
        
        for municipio in municipios:
            if municipio.get('data_ultima_entrega'):
                municipio['data_ultima_entrega'] = municipio['data_ultima_entrega'].strftime('%Y-%m-%d')
            if municipio.get('data_criacao'):
                municipio['data_criacao'] = municipio['data_criacao'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'municipios': municipios,
            'total': len(municipios)
        })
        
    except Error as e:
        print(f"❌ Erro MySQL ao listar municípios: {e}")
        return jsonify({'success': False, 'message': f'Erro no banco de dados: {str(e)}'}), 500
    except Exception as e:
        print(f"❌ Erro geral ao listar municípios: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/municipios', methods=['POST'])
def criar_municipio():
    """Endpoint para criar novo município"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Criando município - Dados recebidos: {data}")
        
        nome = data.get('nome', '').strip()
        total_sementes_kg = data.get('total_sementes_kg', 0)
        total_agricultores = data.get('total_agricultores', 0)
        regiao = data.get('regiao', 'Agreste').strip()
        data_ultima_entrega = data.get('data_ultima_entrega', None)
        
        if not nome:
            return jsonify({'success': False, 'message': 'Nome do município é obrigatório'}), 400
        
        if regiao not in ['Metropolitana', 'Agreste', 'Sertão', 'Zona da Mata']:
            return jsonify({'success': False, 'message': 'Região inválida'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM municipios WHERE nome = %s", (nome,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Município já cadastrado'}), 400
        
        cursor.execute('''
            INSERT INTO municipios (nome, total_sementes_kg, total_agricultores, regiao, data_ultima_entrega) 
            VALUES (%s, %s, %s, %s, %s)
        ''', (nome, total_sementes_kg, total_agricultores, regiao, data_ultima_entrega))
        
        connection.commit()
        print(f"✅ Município criado: {nome}")
        
        return jsonify({
            'success': True, 
            'message': 'Município criado com sucesso!'
        })
        
    except Error as e:
        print(f"❌ Erro MySQL ao criar município: {e}")
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'message': f'Erro no banco de dados: {str(e)}'}), 500
    except Exception as e:
        print(f"❌ Erro geral ao criar município: {e}")
        if connection and connection.is_connected():
            connection.rollback()
        return jsonify({'success': False, 'message': f'Erro interno do servidor: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route('/api/municipios/<int:id>', methods=['PUT'])
def atualizar_municipio(id):
    """Endpoint para atualizar um município existente - CORRIGIDO"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG: Atualizando município {id}: {data}")
        
        nome = data.get('nome', '').strip()
        total_sementes_kg = data.get('total_sementes_kg', 0)
        total_agricultores = data.get('total_agricultores', 0)
        regiao = data.get('regiao', 'Agreste').strip()
        data_ultima_entrega = data.get('data_ultima_entrega', None)
        ativo = data.get('ativo', True)  # ADICIONE ESTA LINHA
        
        if not nome:
            return jsonify({'success': False, 'message': 'Nome do município é obrigatório'}), 400
        
        if regiao not in ['Metropolitana', 'Agreste', 'Sertão', 'Zona da Mata']:
            return jsonify({'success': False, 'message': 'Região inválida'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM municipios WHERE id = %s", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Município não encontrado'}), 404
        
        cursor.execute("SELECT id FROM municipios WHERE nome = %s AND id != %s", (nome, id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Já existe um município com este nome'}), 400
        
        # ATUALIZE A QUERY PARA INCLUIR O CAMPO ativo
        cursor.execute('''
            UPDATE municipios 
            SET nome = %s, total_sementes_kg = %s, total_agricultores = %s, 
                regiao = %s, data_ultima_entrega = %s, ativo = %s
            WHERE id = %s
        ''', (nome, total_sementes_kg, total_agricultores, regiao, data_ultima_entrega, ativo, id))
        
        connection.commit()
        print(f"✅ Município {id} atualizado com sucesso")
        return jsonify({'success': True, 'message': 'Município atualizado com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao atualizar município: {e}")
        return jsonify({'success': False, 'message': f'Erro ao atualizar município: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/municipios/<int:id>', methods=['DELETE'])
def deletar_municipio(id):
    """Endpoint para deletar um município"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        cursor.execute("SELECT id, nome FROM municipios WHERE id = %s AND ativo = TRUE", (id,))
        municipio = cursor.fetchone()
        if not municipio:
            return jsonify({'success': False, 'message': 'Município não encontrado'}), 404
        
        cursor.execute('UPDATE municipios SET ativo = FALSE WHERE id = %s', (id,))
        
        connection.commit()
        print(f"✅ Município {id} deletado com sucesso")
        return jsonify({'success': True, 'message': 'Município excluído com sucesso!'})
        
    except Error as e:
        print(f"❌ Erro ao deletar município: {e}")
        return jsonify({'success': False, 'message': 'Erro ao excluir município'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS DE RELATÓRIOS
# =========================================================================

@app.route('/api/relatorios/entregas-municipio', methods=['GET'])
def relatorio_entregas_municipio():
    """Endpoint específico para relatório de entregas por município"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # ATENÇÃO: Esta query pode falhar porque a tabela 'entregas' não tem 'quantidade_kg'
        cursor.execute('''
            SELECT 
                destino as municipio,
                COUNT(*) as total_entregas,
                SUM(quantidade_kg) as total_sementes_kg, 
                COUNT(DISTINCT motorista) as total_motoristas
            FROM entregas 
            WHERE ativo = TRUE 
            GROUP BY destino
            ORDER BY total_sementes_kg DESC
        ''')
        
        dados = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'dados': dados,
            'total_municipios': len(dados)
        })
        
    except Error as e:
        print(f"❌ Erro ao gerar relatório: {e}")
        return jsonify({'success': False, 'message': 'Erro ao gerar relatório (Verifique se a coluna quantidade_kg existe na tabela entregas ou se precisa de JOIN)'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS DE UTILITÁRIOS
# =========================================================================

@app.route('/api/verificar-email/<email>')
def verificar_email(email):
    """Verifica se email já existe"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'exists': False})
        
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email.lower(),))
        exists = cursor.fetchone() is not None
        return jsonify({'exists': exists})
    except Exception as e:
        print(f"Erro ao verificar email: {e}")
        return jsonify({'exists': False})
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/verificar-banco')
def verificar_banco():
    """Rota para verificar o banco de dados"""
    conn = None
    cursor = None
    try:
        conn = create_connection()
        if not conn:
             return jsonify({'error': 'Não foi possível conectar ao banco'})
             
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        
        cursor.execute("SELECT * FROM remessas")
        remessas = cursor.fetchall()
        
        cursor.execute("SELECT * FROM entregas")
        entregas = cursor.fetchall()
        
        return jsonify({
            'tables': [table[0] for table in tables],
            'total_usuarios': len(usuarios),
            'total_remessas': len(remessas),
            'total_entregas': len(entregas)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/debug/alertas')
def debug_alertas():
    """Rota de debug para verificar a tabela de alertas"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'error': 'Não foi possível conectar ao banco'})
        
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SHOW TABLES LIKE 'alertas'")
        tabela_existe = cursor.fetchone() is not None
        
        if tabela_existe:
            cursor.execute("DESCRIBE alertas")
            estrutura = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as total FROM alertas WHERE ativo = TRUE")
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT * FROM alertas ORDER BY id DESC LIMIT 5")
            registros = cursor.fetchall()
            
            return jsonify({
                'tabela_existe': True,
                'estrutura': estrutura,
                'total_registros': total,
                'ultimos_registros': registros
            })
        else:
            return jsonify({
                'tabela_existe': False,
                'error': 'Tabela alertas não encontrada'
            })
            
    except Error as e:
        return jsonify({'error': f'Erro MySQL: {str(e)}'})
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/debug/tabelas')
def debug_tabelas():
    """Rota para verificar todas as tabelas"""
    connection = None
    cursor = None
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'error': 'Não foi possível conectar ao banco'})
        
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SHOW TABLES")
        tabelas = cursor.fetchall()
        
        cursor.execute("SHOW TABLES LIKE 'municipios'")
        municipios_existe = cursor.fetchone() is not None
        
        resultado = {
            'tabelas': [list(table.values())[0] for table in tabelas],
            'municipios_existe': municipios_existe
        }
        
        if municipios_existe:
            cursor.execute("DESCRIBE municipios")
            resultado['estrutura_municipios'] = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as total FROM municipios")
            resultado['total_registros'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT * FROM municipios LIMIT 5")
            resultado['amostra'] = cursor.fetchall()
        
        return jsonify(resultado)
        
    except Error as e:
        return jsonify({'error': f'Erro MySQL: {str(e)}'})
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================================
# ROTAS PARA ARQUIVOS ESTÁTICOS
# =========================================================================

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/Gestor/<path:filename>')
def serve_gestor(filename):
    return send_from_directory('Gestor', filename)

@app.route('/Cooperativa/<path:filename>')
def serve_cooperativa(filename):
    return send_from_directory('Cooperativa', filename)

@app.route('/Armazem/<path:filename>')
def serve_armazem(filename):
    return send_from_directory('Armazem', filename)

@app.route('/Agente/<path:filename>')
def serve_agente(filename):
    return send_from_directory('Agente', filename)

@app.route('/img/<path:filename>')
def serve_img(filename):
    return send_from_directory('img', filename)

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('css', filename)

# =========================================================================
# INICIALIZAÇÃO DO SERVIDOR
# =========================================================================

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask...")
    print("📊 Inicializando banco de dados...")
    init_database()
    print("✅ Servidor pronto! Acesse: http://localhost:5000")
    app.run(debug=True, port=5000)