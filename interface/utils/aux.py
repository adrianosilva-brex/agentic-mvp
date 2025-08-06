from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv()

class LLMModel(BaseModel):
    model_id: str
    model_name: str
    provider_name: str
    input_modalities: list[str]
    inference_types: list[str]

    # create a pretty print method for this class
    def __str__(self):
        return f"Model ID: {self.model_id}\nModel Name: {self.model_name}"

def build_payload(provider: str, model_id: str, message: str) -> dict:
    print(f"Building payload for {provider} {model_id} {message}")
    if (provider == "anthropic"):
        return {
            "model": model_id,
            "system": "You are a helpful assistant.",
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 2014,
            "stream": False
        }
    else:
        return {
            "model": model_id,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 2014,
            "stream": False
        }


def build_header(provider: str, action: str) -> dict:
    base_header = {}
    if (provider == "anthropic"):
        base_header["x-api-key"] = os.getenv("LLM_GATEWAY_API_KEY")
    else:
        base_header["Authorization"] = f"Bearer {os.getenv('LLM_GATEWAY_API_KEY')}"

    if (action == "fetch_models"):
        return base_header
    else:
        base_header["Content-Type"] = "application/json"
        base_header["x-skip-generative-ai-check"] = "true"
    return base_header

def filter_top_models(models: list[dict]) -> list[dict]:
    """Filter to top 5 models based on variety, status, and capabilities."""
    
    # Define priority models for better variety and capabilities
    priority_models = [
        "anthropic.claude-3-5-sonnet-20241022-v2:0",  # Latest Sonnet v2 (ON_DEMAND)
        "anthropic.claude-3-7-sonnet-20250219-v1:0",   # Newest 3.7 Sonnet
        "anthropic.claude-3-5-haiku-20241022-v1:0",    # Latest fast Haiku
        "anthropic.claude-3-opus-20240229-v1:0",       # Most capable Opus (ON_DEMAND)
        "anthropic.claude-opus-4-20250514-v1:0",       # Latest Opus 4
    ]
    
    # First, try to get all priority models that exist
    filtered = []
    for model_id in priority_models:
        for model in models:
            if model["modelId"] == model_id:
                filtered.append(model)
                break
    
    # If we have less than 5, add more based on criteria
    if len(filtered) < 5:
        remaining_models = [m for m in models if m["modelId"] not in [f["modelId"] for f in filtered]]
        
        # Sort remaining by preference: ACTIVE status, ON_DEMAND inference, newer models
        def model_score(model):
            score = 0
            # Prefer ACTIVE over LEGACY
            if model["modelLifecycle"]["status"] == "ACTIVE":
                score += 100
            # Prefer ON_DEMAND inference types
            if "ON_DEMAND" in model["inferenceTypesSupported"]:
                score += 50
            # Prefer models with IMAGE capability
            if "IMAGE" in model["inputModalities"]:
                score += 20
            # Prefer newer model names (contains higher numbers)
            if "3.5" in model["modelName"] or "4" in model["modelName"]:
                score += 30
            elif "3" in model["modelName"]:
                score += 10
            return score
        
        remaining_models.sort(key=model_score, reverse=True)
        
        # Add up to 5 total models
        for model in remaining_models:
            if len(filtered) >= 5:
                break
            filtered.append(model)
    
    return filtered[:5]