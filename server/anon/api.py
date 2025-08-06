import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_anon_embedded_url(user_id: str, source_provider: str) -> str:
    url = os.getenv("ANON_API_URL") + "api/v1/migration-modal"
    headers = {
        "Authorization": f"Bearer {os.getenv('ANON_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "user_id": user_id,
        "source_provider": source_provider
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["url"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get signed URL: {str(e)}")



def health_check():
    url = os.getenv("ANON_API_URL") + "/healthz"
    headers = {
        "Authorization": f"Bearer {os.getenv('ANON_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return {
            "status": "success",
            "code": response.status_code,
            "data": response.json()
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "code": getattr(e.response, 'status_code', 500),
            "error": str(e)
        }

print(get_anon_embedded_url("adriano.silva@brex.com", "navan"))