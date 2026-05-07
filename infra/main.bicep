// infra/main.bicep
//
// Provisions all Azure infrastructure for the ML API.
// Run once (or re-run on infra changes) before the first CI/CD deploy:
//
//   az group create --name rg-mlapi-prod --location eastus
//   just infra-deploy 'MyStr0ngP@ssword!'
//
// After deployment, copy the printed outputs into GitHub repository secrets:
//   ACR_LOGIN_SERVER      <- acrLoginServer
//   CONTAINER_APP_NAME    <- containerAppName
//   RESOURCE_GROUP        <- (the --resource-group value above)
//   AZURE_CLIENT_ID       <- githubActionsClientId
//   AZURE_TENANT_ID       <- (your Azure AD tenant ID)
//   AZURE_SUBSCRIPTION_ID <- (your subscription ID)

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Short environment tag, e.g. dev or prod.')
@allowed(['dev', 'prod'])
param env string = 'prod'

@description('3-8 char alphanumeric suffix to make globally-unique resource names.')
@minLength(3)
@maxLength(8)
param nameSuffix string

@description('Name of the EXISTING storage account that holds the model blob.')
param storageAccountName string

@description('Blob container name inside the storage account.')
param modelContainerName string

@description('Blob file name of the model artifact, e.g. iris_pipeline.pkl.')
param modelBlobName string

@description('Administrator login for Azure SQL Server.')
param sqlAdminLogin string = 'sqladmin'

@description('Administrator password for Azure SQL Server. Pass at deploy time — do not commit.')
@secure()
param sqlAdminPassword string

@description('GitHub repository in the form owner/repo, used for the CI OIDC federated credential.')
param githubRepo string = ''

// ---------------------------------------------------------------------------
// Derived names and values
// ---------------------------------------------------------------------------

var acrName = 'acr${nameSuffix}'
var sqlServerName = 'sql-mlapi-${nameSuffix}'
var sqlDbName = 'ml_api'
var kvName = 'kv-mlapi-${nameSuffix}'
var logAnalyticsName = 'log-mlapi-${env}'
var containerAppEnvName = 'cae-mlapi-${env}'
var containerAppName = 'ca-mlapi-${env}'
var appIdentityName = 'id-mlapi-app-${env}'
var ciIdentityName = 'id-mlapi-ci-${env}'

var modelBlobUrl = 'https://${storageAccountName}.blob.${environment().suffixes.storage}/${modelContainerName}/${modelBlobName}'

// DB URL stored in Key Vault.
// NOTE: Azure SQL uses Encrypt=yes — not TrustServerCertificate=yes used in local Docker.
// Update alembic.ini and .env accordingly when pointing at this database.
// Bicep masks @secure() parameters in deployment history, so the password is not logged.
var dbUrl = 'mssql+pyodbc://${sqlAdminLogin}:${sqlAdminPassword}@${sqlServerName}.database.windows.net:1433/${sqlDbName}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes'

// ---------------------------------------------------------------------------
// Managed identity for the Container App
// (pulls images from ACR, downloads model from Blob, reads DB URL from Key Vault)
// ---------------------------------------------------------------------------

resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: appIdentityName
  location: location
}

// ---------------------------------------------------------------------------
// Managed identity for GitHub Actions CI
// (pushes images to ACR, updates the Container App)
// ---------------------------------------------------------------------------

resource ciIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: ciIdentityName
  location: location
}

// Federated credential — lets GitHub Actions on the main branch exchange a
// GitHub OIDC token for an Azure access token with no stored secrets.
resource ciFederatedCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = if (!empty(githubRepo)) {
  parent: ciIdentity
  name: 'github-main'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:${githubRepo}:ref:refs/heads/main'
    audiences: ['api://AzureADTokenExchange']
  }
}

// ---------------------------------------------------------------------------
// Log Analytics (required by Container Apps Environment)
// ---------------------------------------------------------------------------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// ---------------------------------------------------------------------------
// Container Apps Environment
// ---------------------------------------------------------------------------

resource containerAppEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Azure Container Registry
// ---------------------------------------------------------------------------

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false  // always use managed identity — never admin credentials
  }
}

// ---------------------------------------------------------------------------
// Azure SQL Server + Database
// ---------------------------------------------------------------------------

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
  }
}

// Allows traffic from other Azure services (including Container Apps).
resource sqlFirewallAllowAzure 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

resource sqlDb 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: sqlDbName
  location: location
  sku: {
    name: 'Basic'
    tier: 'Basic'
    capacity: 5
  }
}

// ---------------------------------------------------------------------------
// Key Vault  (stores DB_URL only — all other config is plain env vars)
// ---------------------------------------------------------------------------

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: kvName
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: tenant().tenantId
    enableRbacAuthorization: true   // use RBAC role assignments, not legacy access policies
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enabledForTemplateDeployment: false
  }
}

resource dbUrlSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'db-url'
  properties: {
    value: dbUrl
  }
}

// ---------------------------------------------------------------------------
// Existing storage account (referenced for the role assignment only)
// ---------------------------------------------------------------------------

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

// ---------------------------------------------------------------------------
// Role assignments
// ---------------------------------------------------------------------------

// AcrPull: Container App identity → ACR
resource appAcrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, appIdentity.id, 'acrpull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// AcrPush: CI identity → ACR
resource ciAcrPushRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, ciIdentity.id, 'acrpush')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8311e382-0749-4cb8-b61a-304f252e45ec')
    principalId: ciIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Contributor: CI identity → resource group (needed for az containerapp update).
// Scope to the resource group rather than the specific Container App to avoid
// a circular dependency (Container App + role assignment created together).
// Tighten to a custom role with only Microsoft.App/containerApps/write if required.
resource ciContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, ciIdentity.id, 'contributor')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')
    principalId: ciIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Storage Blob Data Reader: Container App identity → storage account
resource appStorageBlobReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, appIdentity.id, 'storageblobdatareader')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Key Vault Secrets User: Container App identity → Key Vault
resource appKvSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, appIdentity.id, 'kvsecretsuser')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ---------------------------------------------------------------------------
// Container App
// ---------------------------------------------------------------------------

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${appIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: acr.properties.loginServer
          identity: appIdentity.id
        }
      ]
      // Container Apps Key Vault reference — the secret value is never stored
      // in the Container App config; it is fetched from Key Vault at runtime.
      secrets: [
        {
          name: 'db-url'
          keyVaultUrl: dbUrlSecret.properties.secretUri
          identity: appIdentity.id
        }
      ]
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'ml-api'
          // Placeholder image — CI replaces this on first successful deploy.
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          env: [
            { name: 'ENV', value: env }
            { name: 'APP_NAME', value: 'SampleMLAPI' }
            { name: 'MODEL_BLOB_URL', value: modelBlobUrl }
            { name: 'DB_URL', secretRef: 'db-url' }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
  // The identity must have Key Vault and ACR access before the Container App
  // can start — Bicep resolves ordering via these dependsOn declarations.
  dependsOn: [
    appKvSecretsUserRole
    appAcrPullRole
  ]
}

// ---------------------------------------------------------------------------
// Outputs — copy these into GitHub repository secrets after deployment
// ---------------------------------------------------------------------------

@description('ACR login server. Set as ACR_LOGIN_SERVER GitHub secret.')
output acrLoginServer string = acr.properties.loginServer

@description('Container App name. Set as CONTAINER_APP_NAME GitHub secret.')
output containerAppName string = containerApp.name

@description('Public FQDN of the Container App.')
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn

@description('Client ID of the CI managed identity. Set as AZURE_CLIENT_ID GitHub secret.')
output githubActionsClientId string = ciIdentity.properties.clientId

@description('Key Vault name (for reference).')
output keyVaultName string = keyVault.name

@description('Azure SQL Server FQDN (for reference).')
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
