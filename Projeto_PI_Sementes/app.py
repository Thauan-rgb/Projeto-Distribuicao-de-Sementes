from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import hashlib
import jwt
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)  # Permite requisições do frontend

# Configurações do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Th@203157',
    'database': 'semeia_db'
}

# Chave secreta para JWT
app.config['SECRET_KEY'] = 'sua_chave_secreta_muito_segura_aqui'

def create_connection():
    """Cria conexão com o banco de dados"""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Erro ao conectar com MySQL: {e}")
        return None

def init_database():
    """Inicializa o banco de dados e cria tabelas se não existirem"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Criar tabela de usuários
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
            
            # Criar tabela de remessas
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
            
            # Inserir usuários padrão se não existirem
            usuarios_padrao = [
                ('gerente@ipa.gov.br', 'gerente123', 'gerente'),
                ('cooperativa@ipa.gov.br', 'cooperativa123', 'cooperativa'),
                ('armazem@ipa.gov.br', 'armazem123', 'armazem'),
                ('agente@ipa.gov.br', 'agente123', 'agente')
            ]
            
            for email, senha, tipo in usuarios_padrao:
                # Verificar se usuário já existe
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
                if not cursor.fetchone():
                    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
                    cursor.execute(
                        "INSERT INTO usuarios (email, senha_hash, tipo_usuario) VALUES (%s, %s, %s)",
                        (email, senha_hash, tipo)
                    )
                    print(f"✅ Usuário {email} criado com sucesso!")
            
            connection.commit()
            print("✅ Banco de dados inicializado com sucesso!")
            
        except Error as e:
            print(f"❌ Erro ao inicializar banco: {e}")
        finally:
            cursor.close()
            connection.close()

def hash_password(password):
    """Gera hash da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

# ========== ROTAS DA API ==========

@app.route('/api/login', methods=['POST'])
def login():
    """Endpoint para login"""
    print("=== DEBUG: Endpoint /api/login chamado ===")
    
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
            # Gerar token JWT
            token = jwt.encode({
                'user_id': usuario['id'],
                'email': usuario['email'],
                'tipo': usuario['tipo_usuario'],
                'exp': datetime.utcnow() + timedelta(hours=1)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            # Mapeamento de redirecionamento
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
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/api/criar-senha', methods=['POST'])
def criar_senha():
    """Endpoint para criar nova senha"""
    print("=== DEBUG: Endpoint /api/criar-senha chamado ===")
    
    try:
        data = request.get_json()
        print(f"DEBUG: Dados recebidos: {data}")
        
        email = data.get('email', '').lower().strip()
        nova_senha = data.get('nova_senha', '').strip()
        confirmar_senha = data.get('confirmar_senha', '').strip()
        
        # Validações
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
        
        # Verificar se o email já existe
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Este email já está cadastrado'}), 400
        
        # Determinar tipo de usuário baseado no email
        if 'gerente' in email:
            tipo = 'gerente'
        elif 'cooperativa' in email:
            tipo = 'cooperativa'
        elif 'armazem' in email:
            tipo = 'armazem'
        elif 'agente' in email:
            tipo = 'agente'
        else:
            tipo = 'agente'  # padrão
        
        # Inserir novo usuário
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
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/api/adicionar-remessa', methods=['POST'])
def adicionar_remessa():
    """Endpoint para adicionar nova remessa"""
    print("=== DEBUG: Endpoint /api/adicionar-remessa chamado ===")
    
    try:
        data = request.get_json()
        print(f"DEBUG: Dados recebidos: {data}")
        
        # Extrair dados do formulário
        status = data.get('status', '').strip()
        tipo_semente = data.get('tipo_semente', '').strip()
        numero_lote = data.get('numero_lote', '').strip()
        data_entrada = data.get('data_entrada', '').strip()
        quantidade_kg = data.get('quantidade_kg', '').strip()
        armazem_vinculado = data.get('armazem_vinculado', '').strip()
        criado_por = data.get('criado_por', 'Sistema')
        
        # Validações
        if not all([status, tipo_semente, numero_lote, data_entrada, quantidade_kg, armazem_vinculado]):
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'}), 400
        
        # Converter quantidade para número
        try:
            # Remove 'kg' se existir e converte para float
            quantidade_limpa = quantidade_kg.replace('kg', '').replace('Kg', '').replace('KG', '').strip()
            quantidade_kg_float = float(quantidade_limpa)
        except ValueError:
            return jsonify({'success': False, 'message': 'Quantidade deve ser um número válido'}), 400
        
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Erro no servidor'}), 500
        
        cursor = connection.cursor()
        
        # Verificar se o lote já existe
        cursor.execute("SELECT id FROM remessas WHERE numero_lote = %s", (numero_lote,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Número do lote já existe'}), 400
        
        # Inserir nova remessa
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
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/api/listar-remessas', methods=['GET'])
def listar_remessas():
    """Endpoint para listar todas as remessas"""
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
        
        # Converter datas para string
        for remessa in remessas:
            if remessa['data_entrada']:
                remessa['data_entrada'] = remessa['data_entrada'].strftime('%Y-%m-%d')
            if remessa['data_criacao']:
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
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/api/verificar-email/<email>')
def verificar_email(email):
    """Verifica se email já existe"""
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
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# ========== ROTAS PARA SERVIR ARQUIVOS ESTÁTICOS ==========

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

# ========== VERIFICAR BANCO ==========

@app.route('/api/verificar-banco')
def verificar_banco():
    """Rota para verificar o banco de dados"""
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        # Ver tabelas
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        # Ver usuários
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        
        # Ver remessas
        cursor.execute("SELECT * FROM remessas")
        remessas = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'tables': [table[0] for table in tables],
            'total_usuarios': len(usuarios),
            'total_remessas': len(remessas)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

# ========== INICIALIZAÇÃO ==========

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask...")
    print("📊 Inicializando banco de dados...")
    init_database()
    print("✅ Servidor pronto! Acesse: http://localhost:5000")
    app.run(debug=True, port=5000)