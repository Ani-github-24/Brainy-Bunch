import requests

base_url = "http://localhost:8000"

# 1. Create a class
res_cls = requests.post(f"{base_url}/classes", json={"title": "Test", "subject": "Test", "date": "2026-08-29"})
print("Class:", res_cls.json())
class_id = res_cls.json()["id"]

# 2. Create a session
res_sess = requests.post(f"{base_url}/sessions", json={"class_id": class_id})
print("Session:", res_sess.json())
session_id = res_sess.json()["id"]

# 3. Upload audio
audio_path = r"c:\Users\10124\OneDrive\Documents\Brainy Bunch\audio.mp3"
with open(audio_path, "rb") as f:
    files = {"audio": ("audio.mp3", f, "audio/mpeg")}
    res_transcribe = requests.post(f"{base_url}/sessions/{session_id}/transcribe-chunk", files=files)
print("Transcript:", res_transcribe.json())
