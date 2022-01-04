# How to run deployment for inference routine

We are creating a [managed online (realtime) endpoint](https://docs.microsoft.com/en-us/azure/machine-learning/concept-endpoints#what-are-online-endpoints-preview) for deploying and scoring our machine learning model for hate speech detection. Below is a summary on what values can be changed or added in the yaml definitions for [endpoint.yml](endpoint.yml) and [endpoint-deployment.yml](endpoint-deployment.yml). In addition to the steps to follow in order to be able to deploy the managed online endpoint to Azure using these yaml files.

## What values can be changed or added

* In [endpoint.yml](endpoint.yml)
  * You can change the `name`, but it is important to note that _Endpoint names must be unique within an Azure region. For example, in the Azure westus2 region, there can be only one endpoint with the name my-endpoint._
  * You can change the `auth_mode` from `key` for key-based authentication to `aml_token` for Azure Machine Learning token-based authentication, but it is important to note that _key doesn't expire, but aml_token does expire. (Get the most recent token by using the az ml online-endpoint get-credentials command.)_
  * For other values that can be added based on the requirements, check the YAML syntax [here](https://docs.microsoft.com/en-us/azure/machine-learning/reference-yaml-endpoint-managed-online#yaml-syntax)
* In [endpoint-deployment.yml](endpoint-deployment.yml)
  * You can change the `name`.
  * `endpoint_name` should be the same name used in `endpoint.yml` above.
  * For `model`, we are using a registered model in our Azure Machine Learning Workspace. If you wish to change it to another model, either a registered one or a local one, check the correct syntax [here](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-deploy-managed-online-endpoints#register-your-model-and-environment-separately)
  * `code_configuration` contains the name and the path of the scoring script. You may change the values under it if you change the scoring script path or will use another scoring script.
  * For `environment`, we are using a custom environment in our Azure Machine Learning Workspace. If you wish to change it to another environment, either another online one, a Docker image with Conda dependencies, or a Dockerfile, check the correct syntax [here](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-deploy-managed-online-endpoints#review-the-endpoint-and-deployment-configurations)
  * For `instance_typ`, we are using the cheapest VM SKU to host the deployment, if you wish to change it, check the Managed online endpoints SKU list [here](https://docs.microsoft.com/en-us/azure/machine-learning/reference-managed-online-endpoints-vm-sku-list). For a list of Azure Machine Learning CPU and GPU base images, check [Azure Machine Learning base images](https://github.com/Azure/AzureML-Containers).
  * For `instance_count`, we are using 3 here but it totally depends on the workload you expect. In general, it is recommended to set `instance_count` to at least 3 for high availability.

## Steps to follow for deployment

* First, set the defaults for the Azure CLI, save your default settings. To avoid passing in the values for your subscription, workspace, and resource group multiple times, run this code:

    ```bash
    az account set --subscription <subscription ID>
    az configure --defaults workspace=<Azure Machine Learning workspace name> group=<resource group>
    ```

* Create the endpoint and the deployment using the yaml definitions mentioned above

    ```bash
    az ml online-endpoint create --name <ENDPOINT_NAME> -f endpoint.yml
    az ml online-deployment create --name <DEPLOYMENT_NAME> --endpoint <ENDPOINT_NAME> -f endpoint-deployment.yml --all-traffic
    ```

**_Important Note_**
The `--all-traffic` flag in the above `az ml online-deployment create` allocates 100% of the traffic to the endpoint to the newly created deployment. Though this is helpful for development and testing purposes, for production, you might want to open traffic to the new deployment through an explicit command. For example, `az ml online-endpoint update -n <ENDPOINT_NAME> --traffic "<DEPLOYMENT_NAME>=100"`

## Additional notes/references

* Currently, you can specify only one model per deployment in the YAML. If you have more than one model, when you register the model, copy all the models as files or subdirectories into a folder that you use for registration. In your scoring script, use the environment variable `AZUREML_MODEL_DIR` to get the path to the model root folder. The underlying directory structure is retained.
* Check on managed online endpoints vs Kubernetes online endpoints [here](https://docs.microsoft.com/en-us/azure/machine-learning/concept-endpoints#managed-online-endpoints-vs-kubernetes-online-endpoints-preview)
* Check on the costs for managed online endpoints [here](https://docs.microsoft.com/en-us/azure/machine-learning/concept-endpoints#managed-online-endpoints-vs-kubernetes-online-endpoints-preview)
* Check on deploying and scoring a machine learning model by using a managed online endpoint [here](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-deploy-managed-online-endpoints#prepare-your-system)
