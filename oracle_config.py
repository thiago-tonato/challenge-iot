# Configurações do Oracle Database
# Altere estas configurações conforme seu ambiente Oracle
# Suporta variáveis de ambiente para deploy em Azure

import os

# Configurações de conexão (usa variáveis de ambiente se disponíveis)
ORACLE_CONFIG = {
    'user': os.environ.get('ORACLE_USER', 'rm99404'),
    'password': os.environ.get('ORACLE_PASSWORD', '220205'),
    'host': os.environ.get('ORACLE_HOST', 'oracle.fiap.com.br'),
    'port': int(os.environ.get('ORACLE_PORT', 1521)),
    'service_name': os.environ.get('ORACLE_SERVICE', 'ORCL')
}

# String de conexão DSN (Data Source Name)
def get_dsn():
    return f"{ORACLE_CONFIG['host']}:{ORACLE_CONFIG['port']}/{ORACLE_CONFIG['service_name']}"

# Configurações da tabela
TABLE_NAME = 'detections'
SEQUENCE_NAME = 'detections_seq'
