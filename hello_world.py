from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return "Hello world!"

# .\.venv\Scripts\Activate.ps1 | .\.venv\Scripts\activate.bat
# deactivate
# uvicorn NOME:app --reload