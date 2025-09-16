# 🗄️ Guia Oracle Database

Documentação específica para configuração e uso do Oracle Database no projeto de rastreamento de motos.

## 🎯 Visão Geral

Este projeto utiliza Oracle Database para armazenar dados de rastreamento das motos simuladas, oferecendo robustez, escalabilidade e recursos avançados de análise.

## ⚙️ Configuração do Oracle

### **1. Credenciais de Conexão**

Edite o arquivo `oracle_config.py`:

```python
ORACLE_CONFIG = {
    'user': 'rm99404',                    # Seu usuário Oracle
    'password': '220205',                 # Sua senha
    'host': 'oracle.fiap.com.br',        # Servidor Oracle
    'port': 1521,                        # Porta padrão
    'service_name': 'ORCL'               # Nome do serviço
}
```

### **2. Criação do Usuário (Se Necessário)**

Conecte-se como administrador e execute:

```sql
-- Criar usuário
CREATE USER rm99404 IDENTIFIED BY 220205;

-- Conceder permissões
GRANT CONNECT, RESOURCE TO rm99404;
GRANT CREATE TABLE, CREATE SEQUENCE, CREATE TRIGGER TO rm99404;
GRANT UNLIMITED TABLESPACE TO rm99404;
```

## 🏗️ Estrutura do Banco

### **Tabela Principal: `detections`**

```sql
CREATE TABLE detections (
    id NUMBER PRIMARY KEY,           -- Chave primária auto-incremento
    moto_id NUMBER,                  -- ID da moto (1-4)
    x NUMBER,                        -- Coordenada X
    y NUMBER,                        -- Coordenada Y
    quadrant VARCHAR2(10),           -- Quadrante (A1, B2, etc.)
    timestamp TIMESTAMP              -- Data/hora da detecção
);
```

### **Sequência e Trigger**

```sql
-- Sequência para auto-incremento
CREATE SEQUENCE detections_seq
START WITH 1
INCREMENT BY 1
NOCACHE
NOCYCLE;

-- Trigger para preencher ID automaticamente
CREATE OR REPLACE TRIGGER detections_trg
BEFORE INSERT ON detections
FOR EACH ROW
BEGIN
    IF :NEW.id IS NULL THEN
        :NEW.id := detections_seq.NEXTVAL;
    END IF;
END;
```

## 🔧 Modos de Operação

### **Modo Thick (Recomendado)**
```python
# Requer Oracle Client instalado
oracledb.init_oracle_client()
```

**Vantagens:**
- ✅ Performance superior
- ✅ Recursos avançados
- ✅ Melhor compatibilidade

**Requisitos:**
- Oracle Client 12c ou superior
- Bibliotecas nativas do Oracle

### **Modo Thin (Fallback)**
```python
# Usa apenas bibliotecas Python
# Não requer Oracle Client
```

**Vantagens:**
- ✅ Instalação simples
- ✅ Portabilidade máxima
- ✅ Sem dependências externas

**Limitações:**
- ❌ Performance menor
- ❌ Recursos limitados

## 📊 Consultas Úteis

### **Análise de Movimento**

```sql
-- Últimas posições de todas as motos
SELECT * FROM (
    SELECT moto_id, x, y, quadrant, timestamp
    FROM detections 
    ORDER BY timestamp DESC
) WHERE ROWNUM <= 20;

-- Contagem de detecções por quadrante
SELECT quadrant, COUNT(*) as total_detections
FROM detections 
GROUP BY quadrant 
ORDER BY total_detections DESC;

-- Rota completa de uma moto
SELECT x, y, quadrant, timestamp
FROM detections 
WHERE moto_id = 1 
ORDER BY timestamp ASC;

-- Velocidade média por moto
SELECT moto_id, 
       COUNT(*) as total_movements,
       AVG(SQRT(POWER(LAG(x) OVER (PARTITION BY moto_id ORDER BY timestamp) - x, 2) + 
                POWER(LAG(y) OVER (PARTITION BY moto_id ORDER BY timestamp) - y, 2))) as avg_speed
FROM detections 
GROUP BY moto_id;
```

### **Análise Temporal**

```sql
-- Detecções por hora
SELECT TO_CHAR(timestamp, 'YYYY-MM-DD HH24') as hora,
       COUNT(*) as detections
FROM detections 
GROUP BY TO_CHAR(timestamp, 'YYYY-MM-DD HH24')
ORDER BY hora;

-- Tempo de permanência em cada quadrante
SELECT moto_id, quadrant,
       MIN(timestamp) as entrada,
       MAX(timestamp) as saida,
       (MAX(timestamp) - MIN(timestamp)) * 24 * 60 as minutos_permanencia
FROM detections 
GROUP BY moto_id, quadrant
ORDER BY moto_id, entrada;
```

## 🔍 Troubleshooting

### **Problemas de Conexão**

| Erro | Código | Solução |
|------|--------|---------|
| `DPI-1047` | Cliente não encontrado | Use modo thin ou instale Oracle Client |
| `ORA-01017` | Credenciais inválidas | Verifique usuário/senha no `oracle_config.py` |
| `ORA-12541` | Listener não encontrado | Verifique se Oracle está rodando |
| `ORA-12514` | Serviço desconhecido | Verifique `service_name` |

### **Problemas de Permissões**

| Erro | Solução |
|------|---------|
| `ORA-00942` | Tabela não existe | Execute o script principal para criar |
| `ORA-01031` | Permissões insuficientes | Conceda permissões necessárias |
| `ORA-01950` | Sem espaço em tablespace | Verifique quota do usuário |

### **Teste de Conectividade**

```bash
# Testar conexão
python test_oracle_connection.py

# Verificar status do banco
sqlplus rm99404/220205@oracle.fiap.com.br:1521/ORCL
```

## 📈 Performance e Otimização

### **Índices Recomendados**

```sql
-- Índice para consultas por moto
CREATE INDEX idx_detections_moto_id ON detections(moto_id);

-- Índice para consultas temporais
CREATE INDEX idx_detections_timestamp ON detections(timestamp);

-- Índice para consultas por quadrante
CREATE INDEX idx_detections_quadrant ON detections(quadrant);
```

### **Configurações de Performance**

```sql
-- Configurar tamanho de buffer
ALTER SYSTEM SET db_cache_size = 256M;

-- Configurar conexões simultâneas
ALTER SYSTEM SET processes = 150;
```

## 🔄 Migração de Dados

### **Do SQLite para Oracle**

```bash
# 1. Exportar dados do SQLite
sqlite3 motos.sqlite ".mode csv" ".output detections.csv" "SELECT * FROM detections;"

# 2. Importar para Oracle
sqlldr rm99404/220205@oracle.fiap.com.br:1521/ORCL control=detections.ctl
```

### **Script de Migração**

```python
import sqlite3
import oracledb

# Conectar ao SQLite
sqlite_conn = sqlite3.connect('motos.sqlite')
sqlite_cursor = sqlite_conn.cursor()

# Conectar ao Oracle
oracle_conn = oracledb.connect(
    user='rm99404',
    password='220205',
    dsn='oracle.fiap.com.br:1521/ORCL'
)
oracle_cursor = oracle_conn.cursor()

# Migrar dados
sqlite_cursor.execute("SELECT * FROM detections")
for row in sqlite_cursor.fetchall():
    oracle_cursor.execute("""
        INSERT INTO detections (moto_id, x, y, quadrant, timestamp) 
        VALUES (:1, :2, :3, :4, :5)
    """, row[1:])  # Pula o ID (auto-incremento)

oracle_conn.commit()
```

## 📚 Recursos Adicionais

- [Documentação Oracle Database](https://docs.oracle.com/en/database/)
- [Python-oracledb Documentation](https://python-oracledb.readthedocs.io/)
- [Oracle SQL Reference](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/)
- [Oracle Performance Tuning](https://docs.oracle.com/en/database/oracle/oracle-database/19/tgdba/)

---

**💡 Dica**: Para melhor performance, use o modo thick com Oracle Client instalado e configure índices apropriados.