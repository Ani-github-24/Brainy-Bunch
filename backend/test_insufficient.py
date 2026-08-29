import traceback
from app.studypack import generate_study_pack_content

def test_insufficient_content():
    try:
        # Pass a very short transcript chunk
        generate_study_pack_content([{"seq": 1, "text": "Hello world."}])
        print("FAIL: Expected ValueError to be raised.")
    except ValueError as e:
        if "Insufficient content" in str(e):
            print("SUCCESS: Caught insufficient content error as expected.")
        else:
            print("FAIL: Raised ValueError, but unexpected message:", e)
    except Exception as e:
        print("FAIL: Raised unexpected exception:", type(e), e)

if __name__ == "__main__":
    test_insufficient_content()
