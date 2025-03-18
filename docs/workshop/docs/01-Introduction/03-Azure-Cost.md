# 1.3 Azure Cost Estimate

The Microsoft Azure resources you deploy will be provisioned within your Azure Subscription. You are responsible for the cost of those services. The cost of the solution will vary depending on the Azure region selected and which deployment options you choose.

Most notably, the `deployAMLModel` option you will specify during deployment will impact the overall cost:

- By deploying the Azure Machine Learning model for Semantic Ranker by setting this option to one of the following:
    - `mini` (deploying the ms-marco-MiniLM-L-6-v2 model), the solution will cost approximately $5.50 per day.
    - `bge` (deploying the bge-reranker-v2-m3 model), the solution will cost approximately $17.40 per day.
    - `none` (not deploying semantic re-ranking), the solution will cost approximately $1.10 per day.

The Setup section of this guide will tell you how to choose this deployment option.

Here's a breakout of the _estimated cost_ of Azure resources deployed for this solution:

- Azure ML VM (semantic re-ranking cross encoder model deployment):
    - For ms-marco-MiniLM-L-6-v2 (mini) model running on an STANDARD_D4AS_V4: ~$4.40/day
    - For bge-reranker-v2-m3 (bge) model running on an STANDARD_D16AS_V4: ~$16.30/day
- Azure Database for PostgreSQL: ~$0.90/day
- Azure App Configuration: ~$0.02/day
- Azure Container Registry: ~$0.17/day
- Azure OpenAI Service: Dependent upon usage of Copilot, AI-validation, and number of documents processed in the solution.
- Other services are minimal cost.

To summarize the estimated monthly cost:

- Monthly cost (with mini model) on D-Class 4 vCPU: ~$170.20
- Monthly cost (with bge model) on D-Class 16 vCPU: ~$539.10
- Monthly cost (with no semantic re-ranking): ~$33.80

!!! warning "The above costs are only estimates."

    The costs provided here are estimates based on running the solution accelerator using the provided configuration and are intended to provide general guidance about the costs associated with running the solution accelerator. Depending on deployment options, region selection, and data sizes, individual costs will vary.
