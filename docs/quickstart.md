# Quick start

This guide will walk you through all the steps required to use this repository in your project.

## Prerequisites

You will need the following elements to work with this repository.

1. An Azure Subscription with owner rights.
2. A resource group created under the subcription where all the resources will be placed. If you want to start with a clear resource group, follow the steps [Create a resource group](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/manage-resource-groups-portal#create-resource-groups)
3. An storage account with hierarchical namespaces enabled (aka Azure Data Lake Gen2). This account needs to have a container named `trusted`.

    > Why?: As a best practice, your datasets should not be stored in the resources associated with Azure Machine Learning. Datasets should be part of your Data Platform, not your experimentation platform. The name `trusted` is used as a convention to refer to data clean and steady.

## Create a service principal to run the automation pipelines using such credentials

The automated pipelines provided in this repository will require credentials to do the work. To create a service principal you can follow the steps at [Use the portal to create an Azure AD application and service principal that can access resources](https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal).

> Please take note of the following properties of the service principal: `client id`, `client secret` and `tenant id`.

## Grant the service principal access to the resources

Ensure the service principal created before has the following permissions:

 - At least `Contribute` and `User Access Administrator` acccess to the resource group you created before.

    > **Why?** `Contribute` is needed to deploy all the resources in the resource group automatically by using Infrastructure as code. `User Access Administrator` is required to grant permissions to write secrets in the `Key Vault`. The IaC pipeline will try to modify the permissions to allow the pipelines to store secrets in Key Vault.

 - At least `Contribute` and `Storage Blob Data Reader` access to the Azure Storage Account mentioned as prerequisite in point #3.

    > **Why?** `Storage Blob Data Reader` is needed by Azure Machine Learning to be able to read datasets stored in the blob storage account.

To add role assignments to Azure resources follow the guide: [Assign Azure roles using the Azure portal](https://docs.microsoft.com/en-us/azure/role-based-access-control/role-assignments-portal?tabs=current).

## Next steps

After you are done, you will have to follow some configuration related to the CI/CD implementation. That will depend on the tool you are using. Follow [Quick start guide for Azure DevOps](quickstart-devops.md) and [Quick start guide for GitHub Actions](quickstart-github.md) depending which one you are using.
