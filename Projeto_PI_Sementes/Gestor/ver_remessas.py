import mysql.connector

def ver_remessas():
    try:
        config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'Th@203157',
            'database': 'semeia_db'
        }
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        print("📦 REMESSAS CADASTRADAS:")
        print("=" * 80)
        
        cursor.execute("SELECT * FROM remessas ORDER BY data_criacao DESC")
        remessas = cursor.fetchall()
        
        if remessas:
            for remessa in remessas:
                print(f"ID: {remessa['id']}")
                print(f"Lote: {remessa['numero_lote']}")
                print(f"Tipo: {remessa['tipo_semente']}")
                print(f"Quantidade: {remessa['quantidade_kg']}kg")
                print(f"Status: {remessa['status']}")
                print(f"Armazém: {remessa['armazem_vinculado']}")
                print(f"Criado em: {remessa['data_criacao']}")
                print("-" * 40)
        else:
            print("Nenhuma remessa encontrada!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    ver_remessas()