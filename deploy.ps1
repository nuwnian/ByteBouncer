# ByteBouncer Azure Deployment Automation Script
# This script automates packaging and deploying your Streamlit app to Azure App Service.

# Remove old deployment zip if it exists
if (Test-Path deploy.zip) { Remove-Item deploy.zip }

# Create a new deployment zip with only the necessary files
Compress-Archive -Path bytebouncer,requirements.txt,startup.sh -DestinationPath deploy.zip

# Deploy the zip to Azure App Service
az webapp deploy --resource-group myResourceGroup --name bytebouncerapp --src-path deploy.zip --type zip

# Set the startup command for the app
az webapp config set --resource-group myResourceGroup --name bytebouncerapp --startup-file "startup.sh"
