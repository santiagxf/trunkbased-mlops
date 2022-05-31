# Quick start

This guide will walk you through all the steps required to use this repository in your project. Check the [General architecture](architecture.md) reference for details about the components. .

## Prerequisites

You will need the following elements to work with this repository.

1. An Azure Subscription with owner rights.
2. A resource group created under the subcription where all the resources will be placed. If you want to start with a clear resource group, follow the steps [Create a resource group](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/manage-resource-groups-portal#create-resource-groups)
3. An storage account with hierarchical namespaces enabled (aka Azure Data Lake Gen2). This account needs to have a container named `trusted`.

    > Why?: As a best practice, your datasets should not be stored in the resources associated with Azure Machine Learning. Datasets should be part of your Data Platform, not your experimentation platform. The name `trusted` is used as a convention to refer to data clean and steady.

## Clone or fork the repository

You will need to clone/fork and clone this repository to make the changes specific for your environment. If you are going to use GitHub Actions implementation, you can fork directly on GitHub. If you are planning to use Azure DevOps, you will need to clone the repository in your local machine and then push it to an Azure DevOps respository.

## Create a service principal to run the automation pipelines using such credentials

The automated pipelines provided in this repository will require credentials to do the work. To create a service principal you can follow the steps at [Use the portal to create an Azure AD application and service principal that can access resources](https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal).

> Please take note of the following properties of the service principal: `client id`, `client secret` and `tenant id`.

## Grant the service principal access to the resources

Ensure the service principal created before has the following permissions:

 - At least `Contribute` and `User Access Administrator` acccess to the resource group you created before.

    > **Why?** `Contribute` is needed to deploy all the resources in the resource group automatically by using Infrastructure as code. `User Access Administrator` is required to grant permissions to write secrets in the `Key Vault`. The IaC pipeline will try to modify the permissions to allow the pipelines to store secrets in Key Vault.

 - At least `Storage Blob Data Writer` and `Storage Blob Data Reader` access to the Azure Storage Account mentioned as prerequisite in point #3.

    > **Why?** `Storage Blob Data Reader` is needed by Azure Machine Learning to be able to read datasets stored in the blob storage account. `Storage Blob Data Writer` is needed to initialization of datasets. If you are not initializing datasets, you won't need this last one. (Set `initialize=False` in the Workspace-CD workflow.)

To add role assignments to Azure resources follow the guide: [Assign Azure roles using the Azure portal](https://docs.microsoft.com/en-us/azure/role-based-access-control/role-assignments-portal?tabs=current).

## Configure your Infrastructure as Code

Azure resources are deployed using ARM templates. All the required resources for this sample project are indicated as ARM templates in the directory `.cloud`. Inside this folder you will find:

- `templates` folder: This folder contains all the ARM templates with the details about how to deploy the required resources. The template is generic and parameterized. This has the benefit that you can use the same template with different parameters for different environments. For instance you can deploy the same templates to `dev` using small configurations to save costs and bigger SKUs on `production` to handle the workload demand.
- `dev` folder: This folder represents the paramters of the `development` environment. In this sample, only one environment is indicated but you can create as many environments as you want. 

Open the file `.cloud/dev/deploy.parameters.json` and configure the parameters for your dev environment. The required parameters are:

### Configure the following parameters to deploy new resources

Change the following parameters to unique values for you. The default names are used for the CI/CD of this repository and hence are already taken. You can't use the sames.

 - `location`: Region to deploy resources.
 - `workspaceName`: The name of the Azure ML workspace.
 - `resourceGroupName`: The name of the Azure resource group configured above.
 - `cpuTrainComputeSize`: The VM size of the compute cluster with CPU configuration.
 - `gpuTrainComputeSize`: The VM size of the compute cluster with GPU configuration.
 - `cpuTrainNodeCount`: The max number of nodes in the CPU cluster. To save costs, the cluster has a minimun number of nodes set to 0. This means that if no jobs are being executed, the cluster is deallocated.
 - `gpuTrainNodeCount`: The max number of nodes in the GPU cluster. To save costs, the cluster has a minimun number of nodes set to 0. This means that if no jobs are being executed, the cluster is deallocated.

### Configure the following parameters to use your existing resources

The following configuration keys **are not created by the infrastructure as code** and hence you have to have them created before hand. In the prerequisites section we explained why.

 - `datasetsResourceGroup`: The resource group where the Azure Storage Account used for datasets is placed. **Remember that this Storage Account is not created by the infrastructure as code**, but it is referenced by Azure ML and that's why the information is needed.
 - `datasetsAccountName`: The name of the storage account used for datasets. **Remember that this Storage Account is not created by the infrastructure as code**, but it is referenced by Azure ML and that's why the information is needed.
 - `datasetsFileSystem`: The name of the file system in `datasetsAccountName` to be used. Please use the value `trusted` as datasets are configured to point to this file system.

## Next steps

After you are done, you will have to follow some configuration related to the CI/CD implementation. That will depend on the tool you are using. Follow [Quick start guide for Azure DevOps](quickstart-devops.md) and [Quick start guide for GitHub Actions](quickstart-github.md) depending which one you are using.
