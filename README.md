# 🏍️ Simulador de Rastreamento de Motos IoT

Sistema inteligente de rastreamento de múltiplas motos em tempo real com armazenamento em banco de dados Oracle e visualização interativa.

## 🎯 Visão Geral

Este projeto implementa uma simulação avançada de rastreamento de motos em um ambiente 2D, onde múltiplas motos se movem dinamicamente em um pátio virtual dividido em quadrantes. O sistema coleta dados de posicionamento em tempo real e os armazena em um banco de dados Oracle para análise posterior.

## ✨ Características Principais

### 🚀 **Simulação em Tempo Real**
- **4 motos coloridas** se movendo simultaneamente
- **Grid 5x5** com quadrantes identificados (A1-E5)
- **Física realista** com reflexão nas bordas
- **Visualização OpenCV** com interface gráfica

### 🗄️ **Armazenamento de Dados**
- **Banco Oracle Database** para persistência
- **Detecção automática** de modo thick/thin
- **Timestamps precisos** de cada movimento
- **Histórico completo** de rastreamento

### 📊 **Análise e Visualização**
- **Dashboard web** em `/dashboard` (funciona no navegador/App Service)
- **Dashboard Plotly** local (abre janela quando há display)
- **API Flask REST** completa (endpoints principais)
- **Estatísticas em tempo real**
- **Sistema de status** baseado em quadrantes
- **Alertas em tempo real**

## 🛠️ Tecnologias

- Python 3.11, OpenCV, Oracle Database, Flask, Plotly, Pandas, NumPy

## 📦 Instalação

### 1. **Pré-requisitos**
```bash
# Python 3.8 ou superior
python --version

# Dependências Python
pip install oracledb opencv-python numpy pandas plotly flask
```

### 2. **Configuração do Oracle**
Edite o arquivo `oracle_config.py` com suas credenciais:

```python
ORACLE_CONFIG = {
    'user': 'seu_usuario',
    'password': 'sua_senha', 
    'host': 'oracle.fiap.com.br',
    'port': 1521,
    'service_name': 'ORCL'
}
```

### 3. **Estrutura**

```
challenge-iot/
├── script.py              # Script principal
├── oracle_config.py       # Configurações Oracle
├── requirements.txt       # Dependências
├── Dockerfile            # Container para Azure
└── DEPLOY.md             # Guia de deploy
```

## 🚀 Como Executar

### **Opção 1: Simulação Completa (Recomendado)**
```bash
# Executar simulação com Oracle
python script.py
```

- A API inicia em background e o dashboard web fica disponível em `http://localhost:<PORT>/dashboard` (por padrão, `<PORT>=5000`).
- Em ambientes sem display (ex.: Azure App Service), a janela gráfica não abre; use o dashboard web.

### **Opção 2: Teste de Conexão**
```bash
# Verificar conectividade Oracle
python test_oracle_connection.py
```

### **Opção 3: Demonstração (Sem Oracle)**
```bash
# Executar sem banco de dados
python test_without_oracle.py
```

## 🎮 Controles

- `ESC` - Sair da simulação

## 📊 Banco de Dados

Tabela `detections` com colunas: `id`, `moto_id`, `x`, `y`, `quadrant`, `status`, `timestamp`

Criada automaticamente na primeira execução.

## 🔧 Troubleshooting

- **Erro Oracle**: Verifique credenciais em `oracle_config.py`
- **Módulo não encontrado**: `pip install -r requirements.txt`
- **Porta em uso**: Altere `PORT` no código ou variável de ambiente

## 🌐 Deploy no Azure

Siga o guia rápido para Web App (App Service): [DEPLOY.md](DEPLOY.md)

## 📊 API

Endpoints: `/`, `/dashboard`, `/health`, `/latest`, `/stats`, `/moto/<id>`, `/status`, `/status/<id>`, `/alerts`

Status por quadrante: Colunas 1-2 = `em_uso`, 3 = `no_patio`, 4 = `manutencao`, 5 = `reservada`

### 🔎 Observações de Ambiente
- Em servidores headless (ex.: Azure App Service), a aplicação entra em modo headless automaticamente: a API e a simulação rodam normalmente, mas janelas gráficas (OpenCV/Plotly) não são exibidas. Use o dashboard web em `/dashboard`.

---
