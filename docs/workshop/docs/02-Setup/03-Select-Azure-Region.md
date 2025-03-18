# 2.3 Select An Azure Region

To ensure you can successfully deploy the Azure resources using the `azd up` command, you must choose a region that supports the required Azure OpenAI `gpt-4o` and `text-embedding-ada-002` models, has at least 10K TPM of `Standard` capacity available for each of those models. On completing this step, you should have:

- [X] Selected an Azure region for workshop resources

## Review regional availability and Azure OpenAI quotas

There are only a handful of Azure regions that support all of the required resources and capabilities needed to successfully complete this workshop.

!!! danger "Not selecting an appropriate region will result in a deployment failure!"

Follow the instructions below to review regional availability of the required services, models, and capabilities, and then select one of those for your deployment.

1. Review the regional availability guidance for the [gpt-4o](https://learn.microsoft.com/azure/ai-services/openai/concepts/models?tabs=global-standard%2Cstandard-chat-completions#standard-models-by-endpoint) and [text-embedding-ada-002](https://learn.microsoft.com/azure/ai-services/openai/concepts/models?tabs=global-standard%2Cstandard-embeddings#standard-models-by-endpoint) models in Azure OpenAI.

2. Ensure you have a **at least 10K TPMs of `Standard` capacity available in the region** for both the `gpt-4o` and `text-embedding-ada-002` models. Follow [these instructions](https://learn.microsoft.com/azure/ai-services/openai/how-to/quota?tabs=rest#view-and-request-quota) to check your available quota.

## Select an Azure region that supports workshop resources

1. Based on the regions that meet the requirements from your review above, choose a region that supports **both Azure OpenAI models**, has **adequate `Standard` TPM capacity**.

!!! danger "Select a region that supports both Azure OpenAI models!"

    - Choosing a region that doesn't support both Azure OpenAI models will result in deployment failure when running `azd up`.

    - Selecting a region that does not have at least 10K TPM capacity for both the `gpt-4o` and `text-embedding-ada-002` models will result in a deployment failure when running `azd up`.