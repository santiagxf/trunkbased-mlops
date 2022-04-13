[![workspace-CD](https://santiagxf.visualstudio.com/trunkbased-mlops/_apis/build/status/workspace-CD?branchName=main)](https://santiagxf.visualstudio.com/trunkbased-mlops/_build/latest?definitionId=15&branchName=main)
[![environment-CD](https://santiagxf.visualstudio.com/trunkbased-mlops/_apis/build/status/environment-CD?branchName=main)](https://santiagxf.visualstudio.com/trunkbased-mlops/_build/latest?definitionId=12&branchName=main)
[![model-CD](https://santiagxf.visualstudio.com/trunkbased-mlops/_apis/build/status/model-CD?branchName=main)](https://santiagxf.visualstudio.com/trunkbased-mlops/_build/latest?definitionId=14&branchName=main)

[![workspace-CD](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/workspace-cd.yaml/badge.svg)](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/environment-cd.yaml)
[![environment-CD](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/environment-cd.yaml/badge.svg)](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/environment-cd.yaml)
[![model-CD](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/model-cd.yaml/badge.svg)](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/model-cd.yaml)


# Trunk-based development for Machine Learning models with Azure Machine Learning

This repository contains a working example about how to use trunk-based development git workflow in a Machine Learning project. It demostrates how apply the workflow in a sample project along with a CI/CD implementation for both `Azure DevOps` and `GitHub Acitions` (the implementations are equally capable) for automation and Azure Cloud as our cloud provider.

The resources deployed in `Azure` rely on `Azure Machine Learning`, which is a comprehensive set of tools to boost your work with machine learning projects in `Azure`. To know more about the components of this service you can visit [Get started with Azure Machine Learning](https://azure.microsoft.com/en-us/get-started/services/machine-learning/).


## Motivation

As always, technology is applied in the context of people and processes and there are no exceptions to this rule. A common pitfall when trying to use a git repository in a new ML project is to do so without any clear rules about how the repository should be used or how changes should be posted (committed). In the software development world, this is know as a workflow.

A lot of projects in ML start with a `git` repository, but without a clear strategy about how the repository will serve the goals of the team, and more importantly, how the repository will allow releasing models faster and more reliably. For more details about this topic read the blog: [Put git to work for a Machine Learning projects: How to implement trunk-based development for Machine Learning models projects](https://santiagof.medium.com/put-git-to-work-for-a-machine-learning-projects-8ab79939b88d)

## About this sample

We want to demostrate the power of this approach by using a real world scenario, as close as possible to reality. To do that, we picked a complex enough problem to solve. The objective is to create a model capable of detecting hate speech on text (NLP) coming from tweets in portuguese. The resulting model will be deployed as a REST web service that we can be use for instance to moderate a discussion. Although going over the modeling choices is out side of the scope of this repository, the model used here is based on the `transformers` library from `huggingface`, using `PyTorch` as a backend, and using a BERT-like architecture trained using transfer learning.

In this imaginary scenario (or not), there will be two teams working on the project: the development's team and the operation's team, botth using trunk-based development workflow to collaborate with others in a GitHub repository. The development team will iterate over the model to come up with the best model they can, and placing evaluation routines to decide which model is better and why. They own the source code of the model. The operation's team, on the other hand, uses either `GitHub Actions` or `Azure DevOps` to ensure that the workflow is followed, and the quality of the code is the expected. This allows to implement continuous delivery of the model using a method `champion/challenger` for deciding when to deploy a new version of the model. They own the deployment workflow of the model.

> We named the teams `development's team` and `operation's team` here to avoid the discussion about the details of them. Those team can be composed of `Data Scientist`, `Data Engineers`, `ML Engineers`, `MLOps Engineer`, `Cloud Engineer`, `Architects`, you named. The discussion is outside of the scope of this repository and probably there is not a single good answer about how they have to be composed of.

The repository is structured in a particular way so each time can own specific parts of it. Take into account that this structure is very opinionated and just a way to organize the structure that worked in this scenario. [See the details about how the repository is structured](docs/structure.md) and for a further discussion about why it is structured in this way check my post [Structure your Machine Learning project source code like a pro]().

## Landing trunk-based development in ML projects

Machine Learning models are a combination of data and code. As a consecuence, versioning the code is not enought nor versioning the data. In git workflow, `main` represents the official history of the solution, in our case the model. Trunk-based development demands that `main` should always be deployable, but, how can we make `main` always deployable considering that we want to deploy an ML model? **The model, which is the output of the training process, is the result of combining the model source code with the dataset**. This represents a bigger challenge when we consider that models are rarely versioned control on git. They are usually registered in what is called a *Model Registry*.

### The models' lifecycle

Models are usually version controlled in a model registry, in this case on [Azure Machine Learning's model registry](https://docs.microsoft.com/en-us/azure/machine-learning/concept-model-management-and-deployment). **This means that we won't deploy models from git, but from the registry.**. If you follow this line of thoughts, if we want to make `main` always deployable, that means that `main` always has to have a corresponding model trained and registered in the regitry. On another words, each model version corresponds to a version of main at same point in time.

![](docs/assets/diagrams/model-ci-ct.png)

If we see this in a different perspective, that means that `main` always contains the source code of the last model version since that would make `main` deployable. So now we know that mantaining this relationship between the last version of `main` and the last version of the model in the registry, is all we need to comply with trunk-based development.

> Note that "making main always deployable" doesn’t mean that `main` **is actually always deployed**. The current version of the model in production may be different to the one in main since that depends on how delivery and releasing is happening, which is a different story.

It may be situation where model registration is unwanted for any reason. For those cases, we propose that model registration may require approval in certain environments, like production for instance. This is proposed in our CI/CD implementation.

![](docs/assets/model-ci-ct.png)

### Deployments' lifecycle

Once a model landed in the registry, then we have to make the decision if we want to deploy it or not. In general, this process is called **evaluation**. We want to make this decision independently from how the model is generated so, if at same point we change our minds about how models are evaluated, then we don't have to retrain all the models. If the decision is to deploy, then we should move forward.

![](docs/assets/diagrams/deployment-ci-cd.png)

If we are truly looking to automate this process in the future, then the evaluation process has to be robust enought to take into account multiple factors that can account for the model's performance in general. Although there are multiple ways to achieve this and will definetely depend on the business scenario, this repository will use the following apprach:

- We will use one of the simplest comparison strategies: **champion/challenger**. In this comparison strategy, there is always one model version in production, named **the champion**. The lat model registered in the model registry is called **the challenger**. Each time a model is registered in the registry, a comparison is executed to evaluate if **challenger** is better than **champion**. If this is true, **challenger** will be deployed and take the place of **challenger**.
    - Once you master this strategy you can consider more sophisticated ways like blue/green deployments, progressive rollouts, canary releases, you name it.
- The evaluation will take into account:
    - Point estimates of each model's performance.
        - Since the problem we are solving is a classification problem for hate detection, we will estimate model's performance using `recall`.
    - Statistical analysis the determine is the difference in the point estimates of the performances is statistically significant to justify a deployment.
        - Since the problem we are solving is a classification problem, we are going to use the statistical test **McNemmar** to detect if the performance difference observed in the models didn't occured by chance.

![](docs/assets/deployment-ci-cd.png)

Sometimes, not all the aspects of a model evaluation can be automated and some human-driven evaluation needs to be performed. For instance, checking the errors distribution, revieweing how the model behaves in specific situation, etc. Because of that, manual approval is instructed as part of the evaluation process. Even when the evaluation favors the challenger model, someone has to approve this deployment in order to continue. 

### Datasets' lifecycle

We commonly see a `datasets` folder in git repositories containing the data the models uses for training (actually, this repository has such folder, but here it has a different mission). However, git is not the best place to store this kind of elements as it is not optimized for that for many reasons. So, datasets should be placed outside of git. The location will depend heavily in you complete data state architecture. Such discussions are outside of this repostiory. In our case, the data repository is Azure Data Lake Storage Accounts.

It should not be new to you that a model is the combination of code + data. Code is version-controlled on git, and datasets are version-controlled in whatever the mechanism the storage solution you are using offers. How can make an explicit linkage between the two of them? There are a couple of options here and there is no a single best one, but something we can do is to store datasets configuration on git (pointers).

#### Idea:

Dataset pointers are kept on git. If new datasets are registered, model is not altered until pointing to new version on git. This has some advantages and disadvantages:
- Datasets are static, so reproducibility is enforced.
- You have time to adapt to the new datasets because you can decide which one to use.
- Triggering a retraining requires new commit to update the pointers to the new dataset version. This implies challenges to do automatic retraining.

![](docs/assets/diagrams/datasets-ref.png)

#### How datasets pointers are kept on github?

Azure Machine Learning has the [dataset concept](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-train-with-datasets). Basically, a dataset is a pointer to an storage solution where the data is located. [Azure ML allows to materialize this concept in a `YAML` definition](https://docs.microsoft.com/en-us/azure/machine-learning/reference-yaml-dataset) so as long as we keep this definition on YAML, then we can have a git representation of the dataset in the repository. That's the role of the `datasets` folder, where you will see definitions for 2 datasets:

 - **portuguese-hate-speech-tweets**: The training dataset for hate detection in portuguese.
 - **portuguese-hate-speech-tweets-eval**: The evaluation dataset we use to assess the performance of the models.

> You will see that these datasets also has a folder called `data` inside of them. That's the initialization data so you can have a sample of this data. When datasets are created in Azure ML, we can initialize them using that data so you have something to start with. However, the data is uploaded to the Azure Storage Account you configure during infraestructure deployment.

## Using MLOps to enforce the workflow

We can use MLOps to enforce this workflow and achive automatica integration and deployment (CI/CD). In the folder `.azure-pipelines` (for `Azure DevOps`) and in the folder `.github` (for `GitHub Actions`) you will find the following pipelines available that are pointed out in the workflow. Both implementation are equally capable so you can decide which one is better to use.

| Area             | Workflow/pipeline    | Description                                        | Triggers on |
|------------------|------------------|----------------------------------------------------| ----------- |
| Workspaces       | [Workspace-CD](docs/workflows.md#Workspaces)     | Performs deployments of the Azure Machine Learning resources using Infrastructure as Code (IaC) and ensure workspaces' assets including datasets, data sources and compute clusters. | `main` for changes in path `datasets/*` and `.cloud/*`   | 
| Environments     | [Environment-CI](docs/workflows.md#environment-ci-traininginference-environments-continuous-integration)   | Performs the build and basic validations on the training and inference environments. | PR into `main` on paths `environments/*` |
| Environments     | [Environment-CD](docs/workflows.md#environment-cd-traininginference-environments-continuous-deployment)   | Builds training and inference environments and deploys them on Azure ML | `main` for changes in path `environments/*` |
| Models           | [Model-CI](docs/workflows.md#model-ci-model-continuous-integration)         | Ensures that the model training can be executed in the indicated training environment and that the source code complies with quality standards. | PR into `main` for paths `src/*` and `jobs/*`. |
| Models           | [Model-CT](docs/workflows.md#model-ct-model-continuous-training)         | Responsable for continous training of the model and its corresponding registration in model's registry. This pipeline ensure `main` is always deployable. | `main` for changes in path `src/*` and `jobs/*` |
| Models           | [Model-CD](docs/workflows.md#model-cd-model-continuous-deployment)         | Responsable of the continuos evaluation and deployment of new trained models. | New model registered in the model registry |

### Details

* You can check more details about what actions are performed for each workflow clicking on the link on them or you can [review all the workflow details following this documentation](docs/workflows.md).

* For details about the custom GitHub Actions / Azure DevOps templates used in this implementation check [Custom Actions](docs/actions.md) documentation.

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
