import os
from google import genai
from pydantic import BaseModel, Field

class TestResponse(BaseModel):
    items: list[str] = Field(description="A list of 3 items")

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY'))
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="List 3 random words",
    config=genai.types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=TestResponse,
    )
)
print(response.text)
