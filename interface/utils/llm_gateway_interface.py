try:
    from .aux import LLMModel, filter_top_models, build_header, build_payload
except ImportError:
    from aux import LLMModel, filter_top_models, build_header, build_payload

from dotenv import load_dotenv
import requests
import os

load_dotenv()

def fetch_models(provider: str) -> list[LLMModel]:
    BASE_URL = os.getenv("BREX_LLM_GATEWAY_URL")
    headers = build_header(provider, action="fetch_models")
    gateway_url = f"{BASE_URL}{provider}/v1/models"
    response_models = []
    try:
        response = requests.get(gateway_url, headers=headers)
        response.raise_for_status()
        
        # Filter to top 5 models based on heuristic
        all_models = response.json()
        top_models = filter_top_models(all_models)
        
        for model in top_models:
            new_model = LLMModel(
                model_id=model["modelId"],
                model_name=model["modelName"],  
                provider_name=model["providerName"],
                input_modalities=model["inputModalities"],
                inference_types=model["inferenceTypesSupported"],
            )
            response_models.append(new_model)
        return response_models
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching models from {gateway_url}: {e}")

def send_message(provider: str, model_id: str, message: str) -> str:
    BASE_URL = os.getenv("BREX_LLM_GATEWAY_URL")
    headers = build_header(provider, action="send_message")
    if provider == "anthropic":
        gateway_url = f"{BASE_URL}{provider}/v1/messages"
    else:
        gateway_url = f"{BASE_URL}{provider}/v1/chat/completions"
    
    json = build_payload(provider, model_id, message)
    
    response = requests.post(gateway_url, headers=headers,
                             json=json)
    return response.json()