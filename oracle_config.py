# Configurações do Oracle Database
# Altere estas configurações conforme seu ambiente Oracle

# Configurações de conexão
ORACLE_CONFIG = {
    'user': 'rm99404',
    'password': '220205',
    'host': 'oracle.fiap.com.br',
    'port': 1521,
    'service_name': 'ORCL'
}

# String de conexão DSN (Data Source Name)
def get_dsn():
    return f"{ORACLE_CONFIG['host']}:{ORACLE_CONFIG['port']}/{ORACLE_CONFIG['service_name']}"

# Configurações da tabela
TABLE_NAME = 'detections'
SEQUENCE_NAME = 'detections_seq'
