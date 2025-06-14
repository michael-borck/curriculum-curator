
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test API")

@app.get("/health")
def health():
    return {"status": "healthy", "message": "Test API is running"}

@app.get("/api/workflows")
def list_workflows():
    return {
        "config_workflows": {},
        "predefined_workflows": {
            "test_workflow": {
                "name": "test_workflow",
                "description": "A test workflow for demonstration"
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
