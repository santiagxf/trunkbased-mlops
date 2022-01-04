[![Build Status](https://santiagxf.visualstudio.com/trunkbased-mlops/_apis/build/status/workspace-CD?branchName=main)](https://santiagxf.visualstudio.com/trunkbased-mlops/_build/latest?definitionId=15&branchName=main)
[![Build Status](https://santiagxf.visualstudio.com/trunkbased-mlops/_apis/build/status/environment-CD?branchName=main)](https://santiagxf.visualstudio.com/trunkbased-mlops/_build/latest?definitionId=12&branchName=main)
[![Build Status](https://santiagxf.visualstudio.com/trunkbased-mlops/_apis/build/status/model-CD?branchName=main)](https://santiagxf.visualstudio.com/trunkbased-mlops/_build/latest?definitionId=14&branchName=main)

# Trunk-based development for Machine Learning models with Azure Machine Learning

This repository contains an example about how to use trunk-based development in a Machine Learning project. It demostrates how apply the workflow in a sample machine learning project. The model we implemented here is a hate detection model for tweets in the portuguese language. The repository also contains implementations of CI/CD pipelines to do continuous integration and deployment off all the assets required for the solution using Azure Machine Learning as the ML platform and Azure DevOps as the CI/CD solution. An implementation using GitHub Actions will be posted soon.

## Motivation

As always, technology is applied in the context of people and processes and there are no exceptions to this rule. A common pitfall when trying to use a git repository in a new ML project is to do so without any clear rules about how the repository should be used or how changes should be posted (committed). In the software development world, this is know as a workflow.

For a more in depth introduction an explanation about the need of a git workflow and how trunk-based development works please visit the following post: [Put git to work for a Machine Learning projects: How to implement trunk-based development for Machine Learning models projects](https://santiagof.medium.com/put-git-to-work-for-a-machine-learning-projects-8ab79939b88d)

## Landing trunk-based development in ML projects

Machine Learning models are a combination of data and code. As a consecuence, versioning the code is not enought nor versioning the data. In git workflow, `main` represents the official history of the solution, in our case the model, and should always be deployable. How can we make `main` always deployable considering that what we want to deploy is not the source code but the model? The model itself, which is the output of the training process, is the result of combining the model source code with the data.

Models are usually version controlled in a registry, in this case on Azure Machine Learning model registry. If we want to deploy a model from the registry, then according to trunk-based development it should be on main. This means that each model version corresponds to a version of main at same point in time.

![](docs/assets/main_and_model_version.png)

*Each model version is associated with a given commit in the main branch. That makes main always deployable.*

If we see this in a different perspective, that means that `main` always contains the source code of the last model version since that would make `main` deployable.

> Note that this doesn’t mean that `main` is actually always deployed. The current version of the model in production may be different to the one in main since that depends on how delivery and releasing is happening.

## About the sample model

To ilustrate the use of this repository, we are including a sample project that tries to create a model to detect hate speech in tweet text in portuguese. The models uses `PyTorch` and the `transformers` library from `huggingface` to create a language model based on `BERT`. There are a lot of details about how this model is structured in a way to ensure good coding practices. For more information about that please check [Hate detection model details](docs/model.md)

## CI/CD

In the folder `.azure-pipelines` (for Azure DevOps) and in the folder `.github` (for GitHub Actions) you will find the following pipelines available:

### Workspaces

- **Workspace-CD:** Performs deployments and initialization of some of the elements of the workspace. Particularly:
    - **Infrastructure:** Infraestructure should be deployed by code under IaC. This step will be included soon in the repo. Please create assets manually by the time being.
    - **Datasets:** Ensures that datasets are created and available in the workspace. If they are not, they are initialized with data in the current git repository. For datasets that evolve over time, this pipeline will just create the initial version and the registration. You can leverage tools like Azure Data Factory to move data to the datasets and update the versions. This is outside of the scope of this repository right now but will be shared soon.


### Environments:

- **Environment-CI:** Performs build and basic validations on the environments. All environments in the environments folder will be built and validated.
    - **Triggers on:** Validations for PR into `main`
    - **Actions:**
        - Builds the environment proposed using `conda`
        - Check if the environments already exists in Azure ML and has the right version.
        - Ensure that if the environment details have changed, then a new version is proposed.
- **Environment-CD**: Performs validation and deployment of environments. All environments in the environments folder will be validated.
    - **Triggers on:** `main` for changes in path `environments/*`
    - **Actions:**
        - Check if the environment already exits in Azure ML and has the right version.
        - Look after changes in the environment definition and ensures the right version is used. If any change is introduced, new versions are deployed automatically.
        - Deploy the new version of the environment if needed.

### Models:

- **Model-CI:** Ensures that the model training can be executed and the code complies with standards.
    - **Triggers on:** Validations for PR into `main`
    - **Actions:**
        - Ensure the environment for training exists in Azure ML with the right version.
        - Builds the environment localy.
        - Run lintering.
        - Run unit tests.
        - Create a job for training and capture logs.
        - Publish logs into the assets of the pipeline.
        - Capture metrics, parameters and models and register them in the experiment.
- **Model-CD:** This pipeline is responsable of continuously building and deploying the last version of the model accourding to `main`. 
    - **Triggers on:** `main` for changes in path `src/*` and when new versions of the datasets are available.
    - **Actions:**
        - Stage 1: Model build
            - Ensure the environment for training exists in Azure ML with the right version.
            - Creates a training job and capture logs.
            - Builds the model and compute metrics.
        - Stage 2: Model source control
            - Registers model in the repository and associates it with the run that originated the model.
            - Requires approval in order to registration to happen. This prevents the registration of an unwanted model.

                ![](docs/assets/model-cd-stages-registry.png)
        - Stage 3: Model evaluation
            - Evaluates model performance and detemines if the new model is better than the current one. This CI/CD implementation uses the champion/challenger approach meaning that the currently deployed model is the current champion. Each time a new model is trained, a challenger, it will be evaluated against the current champion. If success, then the challenger would take the place of the champion. Only one model is deployed at a time. If not, a warning will notify that no deployment will happen.

                ![](docs/assets/model-cd-stages-eval.png)
        - Stage 4: Model deployment
            - Deploys the new version of the model and updates the online endpoint.
            - Requires approval in order to deployment to happen.

                ![](docs/assets/model-cd-stages-deploy.png)


For a detail of the actions used to implement this pipelines see [Custom Actions](docs/actions.md).

## Starting using this project

To get yourself started using this repository, please follow the steps at [Quick start](docs/quickstart.md). After you are done, you will have to follow some configuration related to the CI/CD implementation. That will depend on the tool you are using. Follow [Quick start guide for Azure DevOps](docs/quickstart-devops.md) and [Quick start guide for GitHub Actions](docs/quickstart-github.md) depending which one you are using.

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
