#!/usr/bin/env python3
"""
Script de teste para verificar a conexão com Oracle Database
"""

import oracledb
from oracle_config import ORACLE_CONFIG, get_dsn, TABLE_NAME

def test_connection():
    """Testa a conexão com o Oracle Database"""
    try:
        print("Testando conexão com Oracle Database...")
        print(f"Host: {ORACLE_CONFIG['host']}")
        print(f"Port: {ORACLE_CONFIG['port']}")
        print(f"Service: {ORACLE_CONFIG['service_name']}")
        print(f"User: {ORACLE_CONFIG['user']}")
        print(f"DSN: {get_dsn()}")
        print("-" * 50)
        
        # Conecta ao Oracle
        conn = oracledb.connect(
            user=ORACLE_CONFIG['user'],
            password=ORACLE_CONFIG['password'],
            dsn=get_dsn()
        )
        
        print("✅ Conexão estabelecida com sucesso!")
        
        # Testa uma consulta simples
        cur = conn.cursor()
        cur.execute("SELECT SYSDATE FROM DUAL")
        result = cur.fetchone()
        print(f"✅ Data/hora do servidor: {result[0]}")
        
        # Verifica se a tabela existe
        cur.execute(f"""
        SELECT COUNT(*) 
        FROM user_tables 
        WHERE table_name = UPPER('{TABLE_NAME}')
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            print(f"✅ Tabela '{TABLE_NAME}' encontrada!")
            
            # Conta registros na tabela
            cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            count = cur.fetchone()[0]
            print(f"✅ Total de registros na tabela: {count}")
            
            # Mostra alguns registros recentes
            cur.execute(f"""
            SELECT * FROM (
                SELECT * FROM {TABLE_NAME} 
                ORDER BY timestamp DESC
            ) WHERE ROWNUM <= 5
            """)
            recent_records = cur.fetchall()
            print(f"✅ Últimos 5 registros:")
            for record in recent_records:
                print(f"   ID: {record[0]}, Moto: {record[1]}, Pos: ({record[2]}, {record[3]}), Quadrante: {record[4]}, Time: {record[5]}")
        else:
            print(f"⚠️  Tabela '{TABLE_NAME}' não encontrada. Execute o script principal primeiro.")
        
        cur.close()
        conn.close()
        print("✅ Conexão fechada com sucesso!")
        
    except oracledb.Error as e:
        error, = e.args
        print(f"❌ Erro ao conectar com Oracle:")
        print(f"   Código: {error.code}")
        print(f"   Mensagem: {error.message}")
        print(f"   Contexto: {error.context}")
        
        if error.code == 1017:  # Invalid username/password
            print("\n💡 Dica: Verifique as credenciais no arquivo oracle_config.py")
        elif error.code == 12541:  # TNS:no listener
            print("\n💡 Dica: Verifique se o Oracle está rodando e acessível")
        elif error.code == 12514:  # TNS:listener does not know of service
            print("\n💡 Dica: Verifique o nome do serviço no arquivo oracle_config.py")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    test_connection()
