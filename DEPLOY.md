# 🚀 Deploy no Azure - Guia Rápido

## Deploy em 4 Passos

### 1. Login e Criar Recursos

```bash
az login
az group create --name rg-motos-iot --location eastus
az acr create --resource-group rg-motos-iot --name acrmotosiot --sku Basic --admin-enabled true
```

### 2. Build e Push da Imagem

```bash
az acr build --registry acrmotosiot --image motos-iot:latest --file Dockerfile .
```

### 3. Criar Container

```bash
ACR_PASS=$(az acr credential show --name acrmotosiot --query passwords[0].value -o tsv)

az container create \
  --resource-group rg-motos-iot \
  --name motos-iot-mottu \
  --image acrmotosiot.azurecr.io/motos-iot:latest \
  --registry-login-server acrmotosiot.azurecr.io \
  --registry-username acrmotosiot \
  --registry-password $ACR_PASS \
  --dns-name-label motos-iot-mottu \
  --ports 8000 \
  --environment-variables \
    PORT=8000 \
    ORACLE_USER=rm99404 \
    ORACLE_PASSWORD=220205 \
    ORACLE_HOST=oracle.fiap.com.br \
    ORACLE_PORT=1521 \
    ORACLE_SERVICE=ORCL \
  --cpu 2 --memory 4
```

### 4. Obter URL

```bash
az container show --resource-group rg-motos-iot --name motos-iot-mottu --query ipAddress.fqdn -o tsv
```

Acesse: `http://<URL_RETORNADA>:8000`

## Comandos Úteis

```bash
# Ver logs
az container logs --resource-group rg-motos-iot --name motos-iot-mottu --follow

# Reiniciar
az container restart --resource-group rg-motos-iot --name motos-iot-mottu

# Deletar
az container delete --resource-group rg-motos-iot --name motos-iot-mottu
```

