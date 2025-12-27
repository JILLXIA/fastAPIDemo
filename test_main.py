from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_upload_file():
    # Create a dummy file for testing
    file_content = b"This is a test file content."
    files = {"file": ("test_file.txt", file_content, "text/plain")}

    response = client.post("/uploadfile/", files=files)

    assert response.status_code == 200
    assert response.json() == {"filename": "test_file.txt", "content_type": "text/plain"}

