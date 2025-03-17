import os
import logging
import json

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Global variables
model = None
tokenizer = None
device = None

def init():
    """
    Called once when the endpoint container is started.
    Loads model and tokenizer into memory.
    """
    global model, tokenizer, device

    logging.info("Initializing model...")

    # Determine device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Get model directory from Azure ML env variable
    model_dir = os.path.join(os.getenv("AZUREML_MODEL_DIR"), "model-mini")

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.to(device)
    model.eval()

    logging.info("Model initialization complete.")


def run(raw_data):
    """
    Expects input JSON with a 'pairs' field:
    {
      "pairs": [
        ["query", "document 1"],
        ["query", "document 2"]
      ]
    }
    Returns: list of dicts with score and document
    """
    try:
        data = json.loads(raw_data)
        pairs = data.get("pairs", [])

        if not pairs or not isinstance(pairs, list):
            return {"error": "Input JSON must contain a non-empty 'pairs' list"}

        encoded_inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors="pt").to(device)

        with torch.no_grad():
            outputs = model(**encoded_inputs)
            scores = outputs.logits.view(-1).cpu().tolist()

        # Return content alongside score
        results = [
            {"score": score, "content": pair[1]}  # pair[1] = the document
            for score, pair in zip(scores, pairs)
        ]

        return results

    except Exception as e:
        logging.error(f"Error during scoring: {str(e)}")
        return {"error": str(e)}
