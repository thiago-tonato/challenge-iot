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
- **Dashboard Plotly** interativo
- **API Flask** para consultas HTTP
- **Estatísticas em tempo real**
- **Análise de padrões** de movimento

## 🛠️ Tecnologias Utilizadas

- **Python 3.x** - Linguagem principal
- **OpenCV** - Visualização e processamento de imagem
- **Oracle Database** - Armazenamento de dados
- **NumPy** - Computação numérica
- **Pandas** - Manipulação de dados
- **Plotly** - Visualizações interativas
- **Flask** - API web

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

### 3. **Estrutura do Projeto**
```
challenge-iot/
├── script.py                    # 🎮 Script principal
├── oracle_config.py            # ⚙️ Configurações Oracle
├── test_oracle_connection.py   # 🔍 Teste de conexão
├── test_without_oracle.py      # 🧪 Demonstração sem Oracle
├── README.md                   # 📖 Documentação principal
├── README_ORACLE.md            # 🗄️ Guia do Oracle
└── .gitignore                  # 🚫 Arquivos ignorados
```

## 🚀 Como Executar

### **Opção 1: Simulação Completa (Recomendado)**
```bash
# Executar simulação com Oracle
python script.py
```

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

| Ação | Tecla |
|------|-------|
| **Sair da simulação** | `ESC` |
| **Pausar/Continuar** | `SPACE` |
| **Reset posições** | `R` |

## ⚙️ Configurações Avançadas

### **Parâmetros de Simulação**
```python
# Dimensões da janela
WIDTH, HEIGHT = 800, 600

# Grid de quadrantes
GRID_ROWS, GRID_COLS = 5, 5

# Número de motos
NUM_MOTOS = 4

# Cores das motos (BGR)
cores = [(0,0,255), (0,255,0), (255,0,0), (0,255,255)]
```

### **Velocidades e Posições**
```python
# Posições iniciais
xs = [100, 700, 400, 200]
ys = [100, 500, 300, 400]

# Velocidades iniciais
vxs = [3, -2, 4, -3]
vys = [2, -3, -2, 3]
```

## 📊 Estrutura do Banco de Dados

### **Tabela `detections`**
```sql
CREATE TABLE detections (
    id NUMBER PRIMARY KEY,           -- ID auto-incremento
    moto_id NUMBER,                  -- ID da moto (1-4)
    x NUMBER,                        -- Posição X
    y NUMBER,                        -- Posição Y
    quadrant VARCHAR2(10),           -- Quadrante (A1, B2, etc.)
    timestamp TIMESTAMP              -- Data/hora da detecção
);
```

### **Consultas Úteis**
```sql
-- Últimas 10 posições
SELECT * FROM (
    SELECT * FROM detections 
    ORDER BY timestamp DESC
) WHERE ROWNUM <= 10;

-- Contagem por quadrante
SELECT quadrant, COUNT(*) as total
FROM detections 
GROUP BY quadrant 
ORDER BY total DESC;

-- Rota de uma moto específica
SELECT * FROM detections 
WHERE moto_id = 1 
ORDER BY timestamp DESC;
```

## 🔧 Troubleshooting

### **Problemas Comuns**

| Erro | Solução |
|------|---------|
| `DPI-1047: Cannot locate Oracle Client` | Use modo thin (automático) |
| `ORA-01017: invalid username/password` | Verifique credenciais no `oracle_config.py` |
| `ORA-12541: TNS:no listener` | Verifique se Oracle está rodando |
| `ModuleNotFoundError: No module named 'cv2'` | Execute `pip install opencv-python` |

### **Modos de Operação**

#### **Modo Thick (Recomendado)**
- ✅ Melhor performance
- ✅ Recursos avançados do Oracle
- ❌ Requer Oracle Client instalado

#### **Modo Thin (Fallback)**
- ✅ Instalação mais simples
- ✅ Funciona sem Oracle Client
- ❌ Performance menor

## 📈 Funcionalidades Avançadas

### **Dashboard Interativo**
- Gráficos de dispersão das posições
- Análise temporal dos movimentos
- Filtros por moto e quadrante
- Exportação de dados

### **API REST**
```bash
# Últimas detecções
GET /latest

# Estatísticas gerais
GET /stats

# Dados por moto
GET /moto/{id}
```

### **Análise de Dados**
- Padrões de movimento por quadrante
- Velocidade média por moto
- Tempo de permanência em cada área
- Detecção de anomalias

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Autores

- **Desenvolvido para** - Challenge IoT FIAP
- **Tecnologias** - Python, Oracle, OpenCV, IoT

## 📞 Suporte

Para dúvidas ou problemas:
- 📧 Abra uma issue no GitHub
- 📖 Consulte a documentação do Oracle
- 🔍 Verifique os logs de erro

---

**🎯 Objetivo**: Demonstrar capacidades de rastreamento IoT com armazenamento robusto e visualização em tempo real.