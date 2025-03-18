# Exit on error
$ErrorActionPreference = "Stop"

# Download model from Hugging Face
Write-Output "Downloading cross-encoder/ms-marco-MiniLM-L-6-v2 model from Hugging Face.."
$MODEL_DIR = "./scripts/aml/model_asset/model-mini"
New-Item -ItemType Directory -Force -Path $MODEL_DIR

$FILES = @(
 "config.json"
 "pytorch_model.bin"
 "special_tokens_map.json"
 "tokenizer_config.json"
 "vocab.txt"
)
$BASE_URL = "https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2/resolve/main"

foreach ($FILE in $FILES) {
  $FILE_PATH = Join-Path $MODEL_DIR $FILE
  if (-Not (Test-Path $FILE_PATH)) {
    try {
        $content = Invoke-WebRequest -Uri "$BASE_URL/$FILE" -OutFile "$FILE_PATH"
        Write-Output "- $FILE downloaded successfully."
    } catch {
        Write-Error "Failed to download $FILE from $BASE_URL"
    }
  } else {
    Write-Output "- $FILE already exists - skipping download."
  }
}

# Deploy model to Azure Machine Learning Workspace
az account set --subscription "$env:AZURE_SUBSCRIPTION_ID"

# create variable for AML Deployment Name
Write-Output "Creating Azure ML Deployment..."
Write-Output "Workspace:"
Write-Output $env:AZURE_AML_WORKSPACE_NAME
Write-Output "Endpoint:"
Write-Output $env:AZURE_AML_ENDPOINT_NAME
$DEPLOYMENT_NAME = "msmarco-minilm-deployment-6"
$DEPLOYMENT_YML = "./scripts/aml/model_asset/deployment-mini.yml"
az ml online-deployment create --name "$DEPLOYMENT_NAME" --endpoint "$env:AZURE_AML_ENDPOINT_NAME" -f "$DEPLOYMENT_YML" --all-traffic --resource-group "$env:AZURE_RESOURCE_GROUP" --workspace-name "$env:AZURE_AML_WORKSPACE_NAME"