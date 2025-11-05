# 🚀 Deploy no Azure App Service (Web App)

Este guia publica a aplicação Python/Flask como Web App (código), sem containers.

## Pré-requisitos

- Azure CLI instalado e autenticado (`az login`)
- Python 3.11 local e dependências instaladas (`pip install -r requirements.txt`)

## Passo a passo

### 1) Login e grupo de recursos

```bash
az login
az account set --subscription "<SUA_ASSINATURA>"
az group create --name rg-motos-iot --location eastus
```

### 2) Plano App Service Linux e Web App (Python 3.11)

```bash
az appservice plan create \
  --name asp-motos-iot \
  --resource-group rg-motos-iot \
  --sku B1 \
  --is-linux

az webapp create \
  --resource-group rg-motos-iot \
  --plan asp-motos-iot \
  --name motos-iot-mottu \
  --runtime "PYTHON|3.11"
```

### 3) Configurar variáveis de ambiente e comando de inicialização

A aplicação expõe uma API Flask em `script.py` (objeto `app`) e roda a simulação em thread. Para produção no App Service, use Gunicorn:

```bash
az webapp config appsettings set \
  --resource-group rg-motos-iot \
  --name motos-iot-mottu \
  --settings \
    ORACLE_USER="<usuario>" \
    ORACLE_PASSWORD="<senha>" \
    ORACLE_HOST="oracle.fiap.com.br" \
    ORACLE_PORT="1521" \
    ORACLE_SERVICE="ORCL"

# Defina o comando de inicialização para Gunicorn
az webapp config set \
  --resource-group rg-motos-iot \
  --name motos-iot-mottu \
  --startup-file "gunicorn script:app --bind=0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120"
```

Observações:
- O App Service define a variável `$PORT` automaticamente.
- `gunicorn script:app` referencia o objeto Flask `app` declarado em `script.py`.

### 4) Publicar código (Zip Deploy)

Na raiz do projeto (`challenge-iot/`):

**PowerShell:**
```powershell
# Remove zip anterior se existir
Remove-Item app.zip -ErrorAction SilentlyContinue

# Cria zip excluindo .git, __pycache__, venv, etc.
Get-ChildItem -Recurse -File |
  Where-Object {
    $_.FullName -notmatch '\\.git\\' -and
    $_.FullName -notmatch '\\__pycache__\\' -and
    $_.FullName -notmatch '\\.venv\\' -and
    $_.FullName -notmatch '\\venv\\' -and
    $_.Name -ne 'app.zip'
  } |
  Compress-Archive -DestinationPath app.zip -Force

# Deploy
az webapp deploy `
  --resource-group rg-motos-iot `
  --name motos-iot-mottu `
  --src-path app.zip `
  --type zip
```

**Linux/Mac (bash):**
```bash
zip -r app.zip . -x "*.git*" "*__pycache__*" "*.venv*" "*venv*" "*app.zip"
az webapp deploy \
  --resource-group rg-motos-iot \
  --name motos-iot-mottu \
  --src-path app.zip \
  --type zip
```

Se as dependências Python não forem instaladas (erros ModuleNotFoundError), habilite o build durante o deploy:

```bash
az webapp config appsettings set \
  --resource-group rg-motos-iot \
  --name motos-iot-mottu \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true

# Refaça o deploy do zip após isso
az webapp deploy \
  --resource-group rg-motos-iot \
  --name motos-iot-mottu \
  --src-path app.zip \
  --type zip
```

### 5) Verificar URL e logs

```bash
az webapp show \
  --resource-group rg-motos-iot \
  --name motos-iot-mottu \
  --query defaultHostName -o tsv

az webapp log tail \
  --resource-group rg-motos-iot \
  --name motos-iot-mottu
```

Abra: `https://motos-iot-mottu.azurewebsites.net/health`

## Dicas

- Caso prefira comando único, use `az webapp up` na raiz do projeto:

```bash
az webapp up -n motos-iot-mottu -g rg-motos-iot -l eastus --sku B1 --runtime "PYTHON:3.11"
```

- Se precisar usar o servidor Flask nativo (não recomendado), defina o startup para `python script.py`. Prefira Gunicorn.

- OpenCV em servidores: use `opencv-python-headless` (já configurado no `requirements.txt`) para evitar dependências de GUI/`libGL`.

## Limpeza

```bash
az group delete --name rg-motos-iot --yes --no-wait
```

