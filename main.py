from fastapi import FastAPI, UploadFile, File
from langchain_community.document_loaders import WeatherDataLoader
app = FastAPI()

# Get an [API key](https://home.openweathermap.org/api_keys) first.
# Set API key either by passing it in to constructor directly
# or by setting the environment variable "OPENWEATHERMAP_API_KEY".

from getpass import getpass

OPENWEATHERMAP_API_KEY = getpass()

loader = WeatherDataLoader.from_params(
    ["San Jose", "vellore"], openweathermap_api_key=OPENWEATHERMAP_API_KEY
)

@app.get("/")
async def read_root():
    documents = loader.load()
    return {"message": "Hello, FastAPI!", "weather": documents}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename, "content_type": file.content_type}

