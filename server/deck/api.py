import os
from dotenv import load_dotenv

load_dotenv()

def get_embedded_url() -> str:
    return "http://deck.co.mock.url"

def health_check():
    return "OK"