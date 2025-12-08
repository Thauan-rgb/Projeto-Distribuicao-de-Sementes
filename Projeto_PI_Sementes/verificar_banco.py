import mysql.connector

def verificar_banco():
    try:
        # Tente estas configurações (altere a senha)
        configs = [
            {
                'host': 'localhost',
                'user': 'root',
                'password': '',  # Senha vazia (comum no XAMPP)
                'database': 'semeia_db'
            },
            {
                'host': 'localhost',
                'user': 'root', 
                'password': 'root',  # Senha comum
                'database': 'semeia_db'
            },
            {
                'host': 'localhost',
                'user': 'root',
                'password': 'password',  # Outra senha comum
                'database': 'semeia_db'
            },
            {  # ← FALTAVA ESTA VÍRGULA AQUI!
                'host': 'localhost',
                'user': 'root',
                'password': 'Th@203157',  # ← SUA SENHA
                'database': 'semeia_db'
            }
        ]
        
        for config in configs:
            try:
                print(f"🔍 Tentando conectar com: user={config['user']}, password={'*' * len(config['password'])}")
                
                conn = mysql.connector.connect(**config)
                cursor = conn.cursor(dictionary=True)
                
                print("✅ Conexão bem-sucedida!")
                
                # Ver tabelas
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print("📊 TABELAS NO BANCO:")
                for table in tables:
                    print(f"  - {table['Tables_in_semeia_db']}")
                
                # Ver usuários
                print("\n👥 USUÁRIOS CADASTRADOS:")
                cursor.execute("SELECT * FROM usuarios")
                usuarios = cursor.fetchall()
                
                if usuarios:
                    for usuario in usuarios:
                        print(f"  ID: {usuario['id']}")
                        print(f"  Email: {usuario['email']}")
                        print(f"  Tipo: {usuario['tipo_usuario']}")
                        print(f"  Criado em: {usuario['data_criacao']}")
                        print("  " + "-" * 40)
                    print(f"✅ Total de usuários: {len(usuarios)}")
                else:
                    print("  ❌ Nenhum usuário encontrado na tabela 'usuarios'")
                    print("  💡 Execute o Flask novamente para inicializar o banco")
                
                cursor.close()
                conn.close()
                return True
                
            except mysql.connector.Error as e:
                print(f"  ❌ Falha: {e}")
                continue
                
        print("\n🚫 Não foi possível conectar ao MySQL com nenhuma configuração")
        print("💡 Verifique se:")
        print("   - MySQL está instalado e rodando")
        print("   - O banco 'semeia_db' existe") 
        print("   - As credenciais no app.py estão corretas")
        return False
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    verificar_banco()