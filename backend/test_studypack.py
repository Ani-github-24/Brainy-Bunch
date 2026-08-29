import requests
import json

try:
    print("Sending POST request to generate study pack...")
    res = requests.post("http://localhost:8001/sessions/3/generate-study-pack")
    print(f"Status: {res.status_code}")
    data = res.json()
    print("Response JSON keys:", data.keys())

    if "flashcards_json" in data:
        flashcards = json.loads(data["flashcards_json"])
        print("\n--- Example Flashcard ---")
        print(json.dumps(flashcards[0] if flashcards else None, indent=2))
        
        quiz = json.loads(data["quiz_json"])
        print("\n--- Example Quiz Question ---")
        print(json.dumps(quiz[0] if quiz else None, indent=2))

        glossary = json.loads(data["glossary_json"])
        print("\n--- Example Glossary Term ---")
        print(json.dumps(glossary[0] if glossary else None, indent=2))
    else:
        print(data)
except Exception as e:
    print("Error:", e)
