[![workspace-CD](https://santiagxf.visualstudio.com/trunkbased-mlops/_apis/build/status/workspace-CD?branchName=main)](https://santiagxf.visualstudio.com/trunkbased-mlops/_build/latest?definitionId=15&branchName=main)
[![environment-CD](https://santiagxf.visualstudio.com/trunkbased-mlops/_apis/build/status/environment-CD?branchName=main)](https://santiagxf.visualstudio.com/trunkbased-mlops/_build/latest?definitionId=12&branchName=main)
[![model-CD](https://santiagxf.visualstudio.com/trunkbased-mlops/_apis/build/status/model-CD?branchName=main)](https://santiagxf.visualstudio.com/trunkbased-mlops/_build/latest?definitionId=14&branchName=main)

[![workspace-CD](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/workspace-cd.yaml/badge.svg)](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/environment-cd.yaml)
[![environment-CD](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/environment-cd.yaml/badge.svg)](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/environment-cd.yaml)
[![model-CD](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/model-cd.yaml/badge.svg)](https://github.com/csu-devsquad-latam/trunkbased-mlops/actions/workflows/model-cd.yaml)


# Trunk-based development for Machine Learning models with Azure Machine Learning

This repository contains a working example about how to use trunk-based development git workflow in a Machine Learning project. It demostrates how apply the workflow in a sample project along with a CI/CD implementation for both `Azure DevOps` and `GitHub Actions` (the implementations are equally capable) for automation and Azure Cloud as our cloud provider.

The resources deployed in `Azure` rely on `Azure Machine Learning`, which is a comprehensive set of tools to boost your work with machine learning projects in `Azure`. To know more about the components of this service you can visit [Get started with Azure Machine Learning](https://azure.microsoft.com/en-us/get-started/services/machine-learning/).


## Motivation

As always, technology is applied in the context of people and processes and there are no exceptions to this rule. A common pitfall when trying to use a git repository in a new ML project is to do so without any clear rules about how the repository should be used or how changes should be posted (committed). In the software development world, this is know as a workflow.

A lot of projects in ML start with a `git` repository, but without a clear strategy about how the repository will serve the goals of the team, and more importantly, how the repository will allow releasing models faster and more reliably. For more details about this topic read the blog: [Put git to work for a Machine Learning projects: How to implement trunk-based development for Machine Learning models projects](https://santiagof.medium.com/put-git-to-work-for-a-machine-learning-projects-8ab79939b88d)

## About this sample

We want to demostrate the power of this approach by using a real world scenario, as close as possible to reality. To do that, we picked a complex enough problem to solve. The objective is to create a model capable of detecting hate speech on text (NLP) coming from tweets in portuguese. The resulting model will be deployed as a REST web service that we can use, for instance, to moderate a discussion. Although going over the modeling choices is beyond the scope of this repository, the model used here is based on the `transformers` library from `huggingface`, using `PyTorch` as a backend, and using a BERT-like architecture trained using transfer learning.

In this imaginary scenario (or not), there will be two teams working on the project: the development team and the operations team, both using a trunk-based development workflow to collaborate with others in a GitHub repository. The development team will iterate over the model to come up with the best model they can, using evaluation routines to decide which model is better and why. They own the source code of the model. The operations team, on the other hand, uses either `GitHub Actions` or `Azure DevOps` to ensure that the workflow is followed and that the quality of the code is as expected. This allows the ops team to implement continuous delivery of the model using a `champion/challenger` method for deciding when to deploy a new version of the model. They own the deployment workflow of the model.

> We named the teams `development team` and `operations team` here to avoid the discussion about the details of them. The teams can be composed of roles such as `Data Scientist`, `Data Engineer`, `ML Engineer`, `MLOps Engineer`, `Cloud Engineer`, `Architect`, among others. Discussion of team composition is outside the scope of this repository, and probably there is no single good answer about how to compose either the dev or the ops team.

The repository is structured in a particular way so each team can own specific parts of it. Note that this structure is opinionated and is just one way to organize a repo to support this scenario. [See here for details about how the repository is structured](docs/structure.md), and for a further discussion about why it is structured in this way check my post [Structure your Machine Learning project source code like a pro]().

## Trunk-based development in ML projects

Trunk-based development workflow demands that `main` should always be deployable, where `main` represents the official history of the solution, in our case the model. So how can we make `main` always deployable, given that we want to deploy a machine learning (ML) model? An ML model is the result of combining model source code with data. As a consequence, model versioning requires versioning both the code and the data. A challenge unique to MLOps is that only code is directly versioned in the git repo: both the data and resulting model are versioned and tracked by other means. Models, for instance, are typically versioned in what is called a *Model Registry*.

### The model lifecycle

Models are usually version controlled in a model registry, in our case on [Azure Machine Learning's model registry](https://docs.microsoft.com/en-us/azure/machine-learning/concept-model-management-and-deployment). **This means that we won't deploy models from git, but from the registry.**. So if we are following the trunk-based development workflow and thus want to make `main` always deployable, that means that `main` always has to have a corresponding model trained and registered in the registry. In another words, each model version corresponds to a version of main at some point in time.

![](docs/assets/diagrams/model-ci-ct.png)

In particular, `main` should always contain the source code of the last model version, since that would make `main` deployable. So if we manage our workflow in a way that maintains the relationship between the last version of `main` and the last version of the model in the registry, then we will be implementing trunk-based development for ML models.

> Note that "making main always deployable" doesn’t mean that `main` **is actually always deployed**. The current version of the model in production may be different from the one in `main` since model deployment depends on how delivery and release decisions are made, which is a separate issue.

There may be situations where model registration is unwanted. For those cases, we propose that model registration require approval in certain environments, such as in production for instance. This is proposed in our CI/CD implementation.

![](docs/assets/model-ci-ct.png)

### Deployment lifecycle

Once a model lands in the model registry, then we have to make the decision if we want to deploy it or not. In general, this process is called **evaluation**. We want to make this decision independently from how the model is generated so that if at same point we change our minds about how models are evaluated, then we don't have to retrain all the models. If the decision is to deploy, then we should move forward.

![](docs/assets/diagrams/deployment-ci-cd.png)

If we ever want to automate the evaluation process, then the evaluation process has to be robust enough to handle the many factors that can affect model performance across different business scenarios. This repository will use the following approach:

- We will use one of the simplest comparison strategies: **champion/challenger**. In this comparison strategy, there is always one model version in production, named **champion**. The last model registered in the model registry is called **challenger**. Each time a model is registered in the registry, a comparison is executed to evaluate if **challenger** is better than **champion**. If this is true, **challenger** will be deployed and take the place of **champion**.
    - Once you master the champion/challenger strategy you can consider more sophisticated approaches like blue/green deployments, progressive rollouts, canary releases, and others.
- The evaluation will take into account:
    - Point estimates of each model's performance.
        - Since the problem we are solving is a classification problem for hate detection, we will estimate each model's performance using `recall`.
    - Statistical analysis will determine if a difference in recall between the champion and challenger model is significant enough to justify deployment.
        - Since we are building classification models, we are going to use the **McNemar** statistical test to assess whether the performance difference observed between the models may have occured by chance. Only if we detect an improvement in performance unlikely to have occurred randomly will we deploy the challenger model.

![](docs/assets/deployment-ci-cd.png)

Sometimes, not all the aspects of a model evaluation can be automated and some human-driven evaluation is needed. It is common, for instance, to check the error distribution, and to review how the model behaves in specific cases, etc. Because of that, manual approval is included as part of the evaluation process. Even when the evaluation favors the challenger model, someone still has to approve the deployment manually in order for the model deployment to proceed. 

### Datasets lifecycle

Some machine learning git repositories have a `datasets` folder containing the data used for model training. However, git is not the best place to store and version data, for many reasons. Datasets should be placed outside of git. The appropriate location for the data will depend heavily on your data strategy and corresponding architecture, a discussion of which is beyond the scope of this repostiory. In our case, the data repository is an Azure Data Lake Storage account. Our git repository does still have a `datasets` folder, but the data used for training and evaluation is not in that folder; it has a different mission.

As noted above, a model results from a combination of code and data. Code is version-controlled on git. But datasets are version-controlled using mechanisms available in the data storage solution you are using. Since our goal is version-control models, we'll need an explicit linkage between the code versioning and the data versioning. So how can make sure that an explicit linkage between the two of them? There are a couple of options here and there is no a single best one. Our approach here is to store dataset configuration information, or "pointers," on git.

#### Idea:

Dataset pointers are kept on git. If new datasets are registered, the model is not altered until the pointers to the new version of the dataset are updated on git. This has some advantages and disadvantages:
- Datasets are static, so reproducibility is enforced.
- You have time to adapt to the new datasets because you can decide which one to use.
- Triggering a retraining requires a new commit to update the pointers to the new dataset version, which makes automatic retraining more challenging.

![](docs/assets/diagrams/datasets-ref.png)

#### How datasets pointers are kept on GitHub

Azure Machine Learning has the concept of a [Dataset](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-train-with-datasets). Basically, a dataset is a pointer to a storage solution where the data is located. [Azure ML allows us to materialize this concept in a `YAML` definition](https://docs.microsoft.com/en-us/azure/machine-learning/reference-yaml-dataset), so as long as we keep this definition on YAML, then we can have a git representation of the dataset in the repository. That's the role of the `datasets` folder, where you will see definitions for 2 datasets:

 - **portuguese-hate-speech-tweets**: The training dataset for hate detection in portuguese.
 - **portuguese-hate-speech-tweets-eval**: The evaluation dataset we use to assess the performance of the models.

> You will see that these datasets also have a folder called `data` inside of them. That's the initialization data so you can have a sample of this data. When datasets are created in Azure ML, we can initialize them using that data so you have something to start with. However, the data is uploaded to the Azure Storage Account you configure during infrastructure provisioning.

## Using MLOps to enforce the workflow

We can use MLOps to enforce this workflow and achieve continuous integration and continuous deployment (CI/CD). In the folder `.azure-pipelines` (for `Azure DevOps`) and in the folder `.github` (for `GitHub Actions`) you will find the following pipelines available that are referenced in the workflow. Both the `Azure DevOps` and `GitHub Actions` implementations are equally capable, so you can decide which one is better to use.

| Area             | Workflow/Pipeline    | Description                                        | Triggers on |
|------------------|------------------|----------------------------------------------------| ----------- |
| Workspaces       | [Workspace-CD](docs/workflows.md#Workspaces)     | Provisions the Azure Machine Learning resources including datasets, data sources, and compute clusters, using Infrastructure as Code (IaC). | `main` for changes in paths `datasets/*` or `.cloud/*`   | 
| Environments     | [Environment-CI](docs/workflows.md#environment-ci-traininginference-environments-continuous-integration)   | Performs the build and basic validations on the training and inference environments. | PR into `main` on path `environments/*` |
| Environments     | [Environment-CD](docs/workflows.md#environment-cd-traininginference-environments-continuous-deployment)   | Builds training and inference environments and deploys them on Azure ML | `main` for changes in path `environments/*` |
| Models           | [Model-CI](docs/workflows.md#model-ci-model-continuous-integration)         | Ensures that the model training can be executed in the indicated training environment and that the source code complies with quality standards. | PR into `main` for paths `src/*` or `jobs/*`. |
| Models           | [Model-CT](docs/workflows.md#model-ct-model-continuous-training)         | Responsible for continuous training of the model and its corresponding model registration in model registry. This pipeline ensures that `main` is always deployable. | `main` for changes in path `src/*` or `jobs/*` |
| Models           | [Model-CD](docs/workflows.md#model-cd-model-continuous-deployment)         | Responsible of the continuous evaluation and deployment of new trained models. | New model registered in model registry |

### Details

* You can check more details about what actions are performed for each workflow by clicking on the link on them or you can [review the workflow details in this documentation](docs/workflows.md).

* For details about the custom GitHub Actions / Azure DevOps templates used in this implementation check the [Custom Actions](docs/actions.md) documentation.

* Check the [General architecture reference](docs/architecture.md) to know more about the role of each of the components in the architecture.

## Starting using this project

To get yourself started using this repository, please follow the steps at [Quick start](docs/quickstart.md). After you are done, you will have to follow some configuration related to the CI/CD implementation. That will depend on the tool you are using. Follow either [Quick start guide for Azure DevOps](docs/quickstart-devops.md) or [Quick start guide for GitHub Actions](docs/quickstart-github.md), depending which one you are using.


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
