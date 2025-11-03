# Dockerfile para Sistema de Rastreamento de Motos IoT - Mottu
# Azure App Service / Container Instances

FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependências do sistema necessárias para OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (para cache de layers)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Expor porta (Azure usa variável PORT, padrão 8000)
EXPOSE 8000

# Comando de startup
# Para Azure, usar variável PORT ou 8000 como padrão
CMD ["python", "script.py"]

