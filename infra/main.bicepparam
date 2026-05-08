// infra/main.bicepparam
//
// Parameter values for the ML API infrastructure deployment.
// Run once (or re-run on infra changes) with:
//
//   just infra-deploy 'MyStr0ngPassw0rd'
//
// sqlAdminPassword is read from the SQL_ADMIN_PASSWORD environment variable
// so it never touches source control or the process argument list.

using './main.bicep'

param sqlAdminPassword = readEnvironmentVariable('SQL_ADMIN_PASSWORD')

param env = 'prod'

// Container Apps is not available in all regions. eastus has full coverage.
// See: https://azure.microsoft.com/explore/global-infrastructure/products-by-region/
param location = 'westus2'

// Last 6 chars of your subscription ID is a convenient unique suffix.
// Must be 3-8 alphanumeric characters, globally unique across Azure.
param nameSuffix = 'e7c919'

// The storage account you already created that holds the production model.
param storageAccountName = 'irismlapi'
param modelContainerName = 'models'
param modelBlobName = 'iris_pipeline.pkl'

param sqlAdminLogin = 'sqladmin'

// Your GitHub repo in owner/repo form — creates the OIDC federated credential
// so GitHub Actions can authenticate without any stored client secrets.
param githubRepo = 'pablohernandezdo/iris-mlapi'
