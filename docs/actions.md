# Custom actions details

The following actions are available in this repository and allows to build CI/CD pipelines for automation.

- [aml-cli-install](#aml-cli-install)
- [aml-dataset-create](#aml-dataset-create)
- [aml-workspace-get-config](#aml-workspace-get-config)
- [aml-env-build](#aml-env-build)
- [aml-env-ensure](#aml-env-ensure)
- [aml-job-create](#aml-job-create)
- [aml-job-metric-assert](#aml-job-metric-assert)
- [aml-model-register](#aml-model-register)
- [aml-model-compare](#aml-model-compare)
- [aml-model-set](#aml-model-set)
- [aml-endpoint-deploy](#aml-endpoint-deploy)
- [azure-pytest-run](#azure-pytest-run)
- [azure-arm-template-deployment](#azure-arm-template-deployment)
- [pylint-run](#pylint-run)
- [conda-setup](#conda-setup)

> **Note:** On `GitHub Actions` implementation, the parameter `azureServiceConnectionName` is not present as it is only used by `Azure DevOps`. Ignore it from all the actions.

## aml-cli-install

Install the Azure CLI, Azure Machine Learning CLI, and all the required tools. It also configured conda if indicated.

**Inputs**

| Parameter              | Description | Required |
|------------------------|-------------|----------|
| componentSupport       | Indicates if components (aka modules) support should be enabled in the CLI. Defaults to `false` | Yes |
| minVersion             | Minimum version of Azure CLI to install. Defaults to `2.0`.   | Yes |
| pythonTools            | Indicates if Python tools should be installed for Azure ML. Defaults to `false` | Yes |
| pythonVersion          | Python version to use. Defaults to 3.8. | Yes |


**Sample usage**

> Configure Azure ML CLI in preview (2.0) and initializes conda.

```yml
- template: templates/aml-cli-install/step.yaml
  parameters:
    componentSupport: false
    minVersion: 2.0
```

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



## aml-workspace-get-config

Generates the workspace configuration file (`JSON`) for a given Azure Machine Learning Workspace.

**Inputs**

| Parameter     | Description | Required |
|---------------|-------------|----------|
| workspaceName | Name of the workspace to work against. | Yes |
| resourceGroup | Name of the resource group where the workspace is placed. | Yes |
| outputFile    | The path of the `JSON` file to generate. Defaults to `workspace.json`. | No |

**Sample usage**

> Generates the workspace configuration file and names it `workspace.dev.json`.

```yml
- template: templates/aml-workspace-get-config/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
    outputFile: workspace.config.json
```

## aml-dataset-create

Ensure that a given dataset exists in Azure Machine Learning Services. If the dataset doesn't exit, it is created and can be initialized with data which will be uploaded to Azure Storage accounts.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| datasetFile                | Dataset YAML definition file. Wildcard paths are supported. | Yes | 
| initialize                 | Indicates if the dataset should be initialized with same data in the current repository. Defaults to `false`. | No |
| initialDataPath            | Path where the data is located. This path is relative to the location of the dataset YAML definition file. Required if `initialize` is set to `true`. Defaults to `data`. | No |
| storageAccount             | Name of the storage account where data should be uploaded. This storage account should be also registered in Azure Machine Learning as a data store. Required if `initialize` is set to `true`. | No |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |

**Sample usage**

> Creates all the datasets in the folder `datasets` that are specified in a folder structure like `datasets/[datasetname]/dataset.yml`. Datasets are initialized with data stored in the `sample` folder, like ``datasets/[datasetname]/sample/*`.

```yml
- template: templates/aml-dataset-create/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    datasetFile: datasets/*/dataset.yml
    initialize: true
    initialDataPath: sample
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
| name                       | Name of the job to be created. Note that the final name of the job will be the given name followed by the number of the build run `$(Build.BuildId)` or `${{ github.run_id }}`. This value is provided as an output.  | Yes | 
| jobFile                    | Path to the job file. | No |
| stepDisplayName            | Display name of the training job on Azure DevOps. This parameters is not present on GHA. | No |
| useGitMessageForName       | Indicates if the git commit message is used for the display name of the run. Defaults to `true` | No |
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

## aml-job-metric-assert

Asserts that a given metric in a job contains a given value.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| jobName                    | Name of the job where the metric is. | Yes | 
| metric                     | The name of the metric used to compare the models. This metric should be logged in the runs that generated the given models. | Yes |
| expecting                  | Value that you are expecting to have. Any value can be provided from numbers to booleans. | Yes |
| dataType                   | Data type of the expecting value. Possible options are [ `bool`, `boolean`, `numeric`, `float`, `int`, `str`, `string` ] | Yes |
| greaterIsBetter            | Indicates if greater values of the metric `metric` are better. Defaults to `true`. | Yes |
| failureMessage             | Message to display in case the assertion fails. | No |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |
| workspaceConfig            | Workspace configuration file | Yes |

**Outputs**
| Parameter             | Description | isOutput |
|-----------------------|-------------|----------|
| jobMetricAssert.result        | Either `true` or `false` depending if the assertion successed. | Yes | 


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
| fromJob                    | Indicates if the model file will be retrieved from the output of a job. Defaults to `false`. If `true`, then `jobName` should be specified. If `false`, the `modelPath` should be a local file. | Yes |
| fromAnotherWorkspace       | Indicates if the job that created the run is on another workspace that the one that you are trying to register. This is only available in V2 of the actions | No |
| jobName                    | Name of the job from where the model file should be retrieved.  | No |
| modelPath                  | Path to the model file. If `fromJob` is `true`, this is the path inside of the artifacts generated by the run (including the outputs folder). Otherwise it is a local path in the repository. | Yes |
| modelType                  | Type of the model to register. Possible values are `custom_model`, `mlflow_model` and `triton_model`. Defaults to `custom_model` | No |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |

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
| endpoint                   | The path of the endpoint `YAML` file. This is used to infer which is the current version of the model. The first deployment will be used if `deployment` is not indicated. This parameter is required if `champion` is `current`. | No |
| deployment                 | The name of the deployment inside the given endpoint to get the model from. If this parameter is not indicated but an endpoint has been specified, then the first available endpoint is used inside the endpoint. | No |
| compareBy                  | The name of the metric used to compare the models. This metric should be logged in the runs that generated the given models. Defaults to `accuracy` | Yes |
| greaterIsBetter            | Indicates if greater values of the metric `compareBy` are better. Defaults to `true`. | Yes |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |

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

## aml-model-set

Sets a property in an Azure ML Model. Currently, only tags can be set. If the tag is also an MLFlow stage, then it is updated if indicated.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| modelName                  | Name of the model to configure or set.  | Yes | 
| modelVersion               | Version of the model. It can be indicated using a given model version, like 22, or using tokens like `latest` indicating the latest version of the model in the registry. Defaults to `latest`. | Yes |
| property                   | Name of the property you want to set. Properties are treated as `JSON` objects so dot notation works. For instance `tags.state`. | Yes |
| value                      | Value you want to set. | Yes |
| exclusive                  | Indicates if the given value in the given property can be exclusively on one model version only. If this is `true` and other model has the same property value, then it will be remove or replaced. Defaults to `false`. | No |
| replaceExistingWith        | When `exclusive` is `true`, use this parameter to indicate the value you want to change the existing property to. If empty, property is removed. Default to empty. | No. |
| isMlflowStage              | Indicates if the tag correspond to an mlflow stage. Defaults to `false`. | No |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |

**Sample usage**

**#1**
> Sets the property `stage` on model `mymodel` with version `15` to the value `production`. If any other model version has that value, then it is replaced with `surpassed`.

```yml
- template: templates/aml-model-set/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    modelName: mymodel
    modelVersion: 15
    property: stage
    value: production
    exclusive: true
    replaceExistingWith: surpassed
    workspaceName: $(WORKSPACENAME)
    resourceGroup: $(RESOURCEGROUPNAME)
```


## aml-endpoint-deploy

Deploys a model endpoint in Azure Machine Learning Services all along with all the deployments it contains. Logs are collected and uploaded. If traffic is indicted in the `YAML` definition, then traffic of the endpoint is updated accordingly so there is no need to run other commands to do so. If you don't want this to happend, remove the `traffic` option from the `YAML` definition.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes | 
| endpointFile               | Path to the endpoint YAML file. Wildcard paths are supported which means that all matched endpoints will be deployed  | Yes | 
| deploymentFile             | Path to the deployment YAML files for the given endpoints. This path is relative to the path where the endpoints are located. Model versions in these YAML files can be indicated as supported by Azure ML using the version number (ej: `azureml:hate-pt-speech:22`) or by using an enhanced schema with tokens `latest` (`azureml:hate-pt-speech:latest`) and `current` (`azureml:hate-pt-speech:current`). `latest` resolves to the latest version of the model registered and `current` resolves to the current version of the model deployed in the given endpoint/deployment. Note that this schema is not supported OOTB by Azure ML. Wildcard paths are supported. | Yes |
| modelVersion               | Model version you want to deploy. If this specified, it will overwrite the version indicated in the deployment file. Otherwise, the one indicated there will be used. | No |
| workspaceName              | Name of the workspace to work against. | Yes |
| resourceGroup              | Name of the resource group where the workspace is placed. | Yes |
| noWait                     | Indicates if the action should not wait for the deployment to finish. If `true`, logs are not captured. Default to `false`. | No |
| args                       | Any extra argument you want to pass to the endpoint deployment command. For instance, `--local`. | No |
| secretsToKeyVault          | Indicates if the `scoring url` and the `scoring key` should be uploaded to Azure Key Vault. Secrets naming convention is `<ENDPOINT_NAME>_scoringUrl` and `<ENDPOINT_NAME>_scoringKey` | No |
| keyVaultName               | The name of the key vault to use. Required if `secretsToKeyVault` is `true`. | No | 

**Sample usage**

> Deploys the endpoint specified in the file `endpoints\mymodel\endpoint.yml`. All the deployments that are in `endpoints\mymodel\deployments` will be deployed for the given endpoint. Secrets will be uploaded to the key vault with name `my-keyvault`.

```yml
- template: templates/aml-endpoint-deploy/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    endpointFile: endpoints/mymodel/endpoint.yml
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
| args                       | Parameters, if any, to provide to the execution. For instance, to provide test parameters you can use `-q --param1=value1 --param2=value2` | No |

**Sample usage**

**#1**
> Runs `PyTest` for code in folder `src`. Uses a conda environment named `cicd`. This environment should be created beforehand.

```yml
- template: templates/azure-pytest-run/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    source: src
    useConda: true
    condaEnvName: cicd
```

**#2**
> Runs `PyTest` for code in folder `src`. Tests recieves a parameter named `input-file`.

```yml
- template: templates/azure-pytest-run/step.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    source: src
    args: -q --input-file=mydata.json
```

## azure-arm-template-deployment

Deploys resources using ARM templates at the resource group level.

**Inputs**

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| azureServiceConnectionName | Service connection used to connect with Azure. | Yes |
| resourceGroup              | Resource group where resources will be placed.  | Yes | 
| location                   | Location where resources will be placed. See Azure supported regions for a list of possibe values | Yes |
| deploymentName             | Display name for the deployment. | Yes |
| template                   | `JSON` ARM template. This template will be created as a Template resource in the resource group mentioned. | Yes |
| Version                    | Version of the template your are creating. Defaults to `1.0`. | No |
| parameters                 | `JSON` ARM template parameters file. If parameters of type `secureString` are specified, pass them here. Use the format `parameter1=value1 parameter2=value2`. | No |

**Sample usage**

> Deploy resources with `secureString` paramters.

```yml
- template: templates/azure-arm-template-deployment/action.yaml
  parameters:
    azureServiceConnectionName: $(SERVICECONNECTION)
    resourceGroup: my-resourcegroup-dev
    location: eastus2
    deploymentName: mydeployment
    template: workspaces/templates/deploy.json
    version: 1.0
    parameters: workspaces/dev/deploy.parameters.json computeAdminUserName=$(computeAdminUserName) computeAdminUserPassword=$(computeAdminUserPassword)
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

# conda-setup

Installs and setup conda to work in the agent.

| Parameter                  | Description | Required |
|----------------------------|-------------|----------|
| condaFile                  | Conda file for the environment to create, if any. | No |
| activate                   | Inidicates if the environment has to be activated. If no environment is provided, this affects the `base` environment. Defaults to `false` | No | 
| envName                    | Name of the environemnt to create, if any. This name is used if a name is also indicated in `condaFile`. | No |
| python                     | Version of `Python` to use. If a `conda file` is provided, then the one indicated there is used. Defaults to `3.8` | No |

**Remarks**

On Github Actions, agents execute bash without a profile and hence, if you try to run `conda activate` you will recieve the error `conda is not initialized`. To workaround this problem, if you want to use later `conda activate` run `source $CONDA/etc/profile.d/conda.sh` before to ensure proper initialization of `conda` in your shell.

**Sample usage**

**#1**
> Initialize conda but no environment is created.

```yml
- template: templates/conda-setup/step.yaml
```

**#2**
> Initialize conda and create an environment from a file.

```yml
- template: templates/conda-setup/step.yaml
  parameters:
    condaFile: conda_dependencies.yml
    activate: true
```

**#3**
> Initialize conda and create an environment from scratch with `Python` version `3.8`.

```yml
- template: templates/conda-setup/step.yaml
  parameters:
    envName: myproject
    activate: true
    python: 3.9
```