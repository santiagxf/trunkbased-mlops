# Custom actions details

The following actions are available in this repository and allows to build CI/CD pipelines for automation.

## aml-env-build

Builds an Azure ML Environment in the local instance using `conda` and checks that the builds are completed without errors. If a library can't be installed, this action will fail. Note that this build action only can build environments inside the agent running the action. Building the environment in a `container` is not supported by the moment but in roadmap.

**Inputs**

| Parameter     | Description | Required |
|---------------|-------------|----------|
| envFile       | Path to the environment file to build. Note that this is not the `conda_dependencies.yml` file. Wildcards paths are supported. | Yes | 


**Sample usage**

> Builds the environment definition at `environments/myenv/environment.yml`.

```yml
- template: templates/aml-env-build/step.yaml
  parameters:
    envFile: environments/myenv/environment.yml
```

## aml-env-ensure

Ensures or checks that a given Azure ML Environment exists on Azure. Checks if it can be correctly deployed on the target Azure ML Workspace and checks if there were alterations in the conda dependencies file that requires a new version of the environment to be deployed. That means that any change in the environment definition will be captured and failed if they don't match with the registered version.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| envFile                    | Path to the environment file. Note that this is not the `conda_dependencies.yml` file. Wildcards are supported. | Yes | 
| validateOnly               | Indicates if only validations should be performed. If `true`, no environment will be created in Azure ML if environment or environment version is not deployed yet. Defaults to `false`. | Yes |
| failOnMissing              | Indicates if the job should fail if an environment is missing on Azure ML Workspace but it will be successfuly deployed if `validateOnly` is `false`. This parameter is ignored if `validateOnly` is `false` as deployment will occur if an environment is missing. It is useful when implementing CI jobs. Defaults to `true`. | No |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |

**Sample usage**

**#1**
> Checks that the environment indicated in `environments/my-env/environment.yml` is correct. Only performs validation and if the environment is missing, the action won't fail but it will notify. This will be suitable for a CI workflow.

```yml
- template: templates/aml-env-ensure/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    envFile: environments/my-env/environment.yml
    validateOnly: true
    failOnMissing: false
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
```

**#2**
> Checks that all the environments indicated in folder `environments` are correct. Only performs validation and if an environment is missing, the action won't fail but it will notify. This will be suitable for a CI workflow.

```yml
- template: templates/aml-env-ensure/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    envFile: environments/*/environment.yml
    validateOnly: true
    failOnMissing: false
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
```

**#3**
> Deploys and check all the environments indicated in folder `environments`. This will be suitable for a CD workflow.

```yml
- template: templates/aml-env-ensure/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    envFile: environments/*/environment.yml
    validateOnly: false
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
```

## aml-dataset-create

Ensure that a given dataset exists in Azure Machine Learning Services. If the dataset doesn't exit, it is created and can be initialized with data which will be uploaded to Azure Storage accounts.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| datasetFile                | Dataset YAML definition file. Wildcard paths are supported | Yes | 
| initialize                 | Indicates if the dataset should be initialized with same data in the current repository. Defaults to `false`. | No |
| initialDataPath            | Path where the data is located. This path is relative to the location of the dataset YAML definition file. Required if `initialize` is set to `true`. Defaults to `data`. | No |
| storageAccount             | Name of the storage account where data should be uploaded. This storage account should be also registered in Azure Machine Learning as a data store. Required if `initialize` is set to `true`. | No |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |

**Sample usage**

> Creates all the datasets in the folder `datasets` that are specified in a folder structure like `datasets/[datasetname]/dataset.yml`. Datasets are initialized with data stored in the `data` folder, like ``datasets/[datasetname]/data/*`.

```yml
- template: templates/aml-dataset-create/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    datasetFile: datasets/*/dataset.yml
    initialize: true
    initialDataPath: data
    storageAccount: $(STORAGEACCOUNTNAME)
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
```

## aml-job-create

Creates and submit a new job to Azure ML based on a job configuration. Jobs are named using the provided job name and a unique run id returned by Azure DevOps.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| name                       | Name of the job to be created. Note that the final name of the job will be the given name followed by the number of the build run `$(Build.BuildId)`. THhis value is provided as an output.  | Yes | 
| jobFile                    | Path to the job file. | No |
| noWait                     | Indicates if the pipeline should wait for the job to finish. If `false`, then the job will capture the output of the job and publish the logs as an asset in the pipeline run. Defaults to `false`. | No |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |


**Outputs**
| Parameter             | Description | isOutput |
|-----------------------|-------------|----------|
| jobRun.jobName        | Name of the job name created in the workspace. | Yes | 


**Sample usage**

> Creates a new job with name `my-classifier-experiment-[BUILD_ID]` using the job file in `jobs/my-classifier/train.job.yml`. The action will wait till the job is done.

```yml
- template: templates/aml-job-create/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    name: my-classifier-experiment
    jobFile: jobs/my-classifier/train.job.yml
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
    noWait: false
```

## aml-model-register

Registers a new model in the workspace.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| name                       | Name of the model.  | Yes | 
| description                | Description of the model. It can be any string. | No |
| fromJob                    | Indicates if the model file will be retrieved from the output of a job. Defaults to `false`. If `true`, then `jobName` should be specified. If `false`, the `modelPath` should be a local file. | No |
| jobName                    | Name of the job from where the model file should be retrieved.  | No |
| modelPath                  | Path to the model file. If `fromJob` is `true`, this is the path inside of the artifacts generated by the run (including the outputs folder). Otherwise it is a local path in the repository. | Yes |
| modelVersion               | Version of the model to register. Currently, this parameters is provided for backward-compatibility with previous version of the action. Latest version is always used. | No |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |
| workspaceConfig            | Configuration file of the workspace where to register the model | Yes |

**Outputs**
| Parameter                 | Description | isOutput |
|---------------------------|-------------|----------|
| modelRegistration.version | Version of the model just registered. | Yes | 

**Sample usage**

> Registers a model named `my-classifier`. The model file is extracted from the job with name `my-classifier-job-152` which generated the model and stored in the folder `outputs/my-classifier.pkl`. This is a path inside the experiments artifacts.

```yml
- template: templates/aml-model-register/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    name: my-classifier
    fromJob: true
    jobName: my-classifier-job-152
    description: "A sample classifier"
    modelPath: outputs/my-classifier.pkl
    modelVersion: latest
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
    workspaceConfig: workspaces/dev/workspace.json
```

## aml-model-compare

Compares two model versions, a champion and a challenger, based on a given metric and indicates if the challenger model, acting a the new model, is better than the current champion, acting as the current deployed model. This method is usually called champion/challenger comparison. Metrics of the models should be logged in the run that generated them. This implies that model registration should always indicate the Run ID that generated the model.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| modelName                  | Name of the model.  | Yes | 
| champion                   | Version of the model that is acting as the champion. It can be indicated using a given model version, like 22, or using tokens like `current` indicating the current deployed version in a given endpoint/deployment. If indicated with `current`, then `endpoint` parameter should be specified. If `current` is indicated and there is no model deployed in `endpoint` then the comparison will always vote for challenger. | Yes |
| challenger                 | Version of the model that is acting as the challenger. It can be indicated using a given model version, like 22, or using tokens like `latest` indicating the latest version of the model in the registry. Defaults to `latest`. | Yes |
| endpoint                   | The name of the endpoint where the model is being deployed later. This is used to infer which is the current version of the model. The first deployment will be used if `deployment` is not indicated. This parameter is required if `champion` is `current`. | No |
| compareBy                  | The name of the metric used to compare the models. This metric should be logged in the runs that generated the given models. Defaults to `accuracy` | Yes |
| greaterIsBetter            | Indicates if greater values of the metric `compareBy` are better. Defaults to `true`. | Yes |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |
| workspaceConfig            | Configuration file of the workspace | Yes |

**Outputs**
| Parameter                 | Description | isOutput |
|---------------------------|-------------|----------|
| compare.result | Either `true` or `false` depending if the comparison favored `challenger` over `champion`. | Yes | 

**Sample usage**

**#1**
> Compares if the version `15` of the model `my-classifier` is better than the version `10` using the metric `loss`.

```yml
- template: templates/aml-model-compare/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    modelName: my-classifier
    champion: 10
    challenger: 15
    compareBy: loss
    greaterIsBetter: false
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
    workspaceConfig: workspaces/dev/workspace.json
```

**#2**
> Compares if the latest version of the model `my-classifier` is better than the current version of the model deployed in the endpoint indicated in `endpoints/my-classifier/endpoint.yml`. Since no deployment is indicated, the first one is used. Metric used is `eval_recall`.

```yml
- template: templates/aml-model-compare/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    modelName: my-classifier
    champion: current
    challenger: latest
    endpoint: endpoints/my-classifier/endpoint.yml
    compareBy: eval_recall
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
    workspaceConfig: workspaces/dev/workspace.json
```

## aml-endpoint-deploy

Deploys a model endpoint in Azure Machine Learning Services all along with all the deployments it contains. Logs are collected and uploaded.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| endpointFile               | Path to the endpoint YAML file. Wildcard paths are supported which means that all matched endpoints will be deployed  | Yes | 
| deploymentFile             | Path to the deployment YAML files for the given endpoints. This path is relative to the path where the endpoints are located. Model versions in these YAML files can be indicated as supported by Azure ML using the version number (ej: `azureml:hate-pt-speech:22`) or by using an enhanced schema with tokens `latest` (`azureml:hate-pt-speech:latest`) and `current` (`azureml:hate-pt-speech:current`). `latest` resolves to the latest version of the model registered and `current` resolves to the current version of the model deployed in the given endpoint/deployment. Note that this schema is not supported OOTB by Azure ML. Wildcard paths are supported. | Yes |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |
| noWait                     | Indicates if the action should not wait for the deployment to finish. If `true`, logs are not captured. | Yes |
| secretsToKeyVault          | Indicates if the `scoring url` and the `scoring key` should be uploaded to Azure Key Vault. | No |
| keyVaultName               | The name of the key vault to use. Required if `secretsToKeyVault` is `true`. | No | 

**Sample usage**

> Deploys all the endpoints in the folder `endpoints\[endpointname]` with file names `endpoint.yml`. On top of that, all the deployments for each endpoints that are in `endpoints\[endpointname]\deployments` will be deployed. Secrets will be uploaded to the key vault with name `my-keyvault`.

```yml
- template: templates/aml-endpoint-deploy/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    endpointFile: endpoints/*/endpoint.yml
    deploymentFile:  deployments/*.yml
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
    secretsToKeyVault: true
    keyVaultName: my-keyvault
```

## azure-pytest-run

Run `pytest` tests that may rely on Azure and hence they are executed in the context of an authenticated console. Tests can get the authentication token from it if needed.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| source                     | Directory where the source code is located. Defaults to current directory `.` | Yes |
| configuration              | PyTest configuration file path (.ini).  | No | 
| useConda                   | Indicates if the tests will run using an specific conda environment. Defaults to `false`. | No |
| condaEnvName               | Name of the conda environment to use. Required if `useConda` is `true`. | No |
| testFolder                 | Folder where test are placed. Defaults to `tests`. | No |
| version                    | PyTest library version. Defaults to `6.2.5`. | Yes |

**Sample usage**

> Runs `PyTest` for code in folder `src`. Uses a conda environment named `cicd`. This environment should be created beforehand.

```yml
- template: templates/azure-pytest-run/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    source: src
    useConda: true
    condaEnvName: cicd
```

## pylint-run

Run lintering over the source code. 

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| source                     | Directory where the source code is located. Defaults to current directory `.` | Yes |
| moduleOrPackage            | Module or package over which to run lintering. Defaults to `*`, meaning all the modules will be evaluated.  | Yes | 
| useConda                   | Indicates if the tests will run using an specific conda environment. Defaults to `false`. | No |
| condaEnvName               | Name of the conda environment to use. Required if `useConda` is `true`. | No |
| disable                    | Indicates which rules should not be checked. Coma separeted values are possible. Defaults to empty. | No |
| pkgWhitelist               | Indicates which packages should not be checked for lintering. | No |

**Sample usage**

> Runs `PyLint` for code in folder `src`. All the code is evaluated. Rules `W1023` and `C0103` are not validated. Uses a conda environment named `cicd`. This environment should be created beforehand.

```yml
- template: templates/pylint-run/step.yaml
  parameters:
    source: src
    useConda: true
    condaEnvName: cicd
    disable: W1203,C0103
```
