import os
import sys

def list_models(api_key):
    from google import genai
    client = genai.Client(api_key=api_key)
    for m in client.models.list():
        print(m.name)

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if len(sys.argv) > 1:
        key = sys.argv[1]
    
    if not key:
        print("ERROR: No API key provided.")
        sys.exit(1)
        
    list_models(key)
