from fastapi import FastAPI

app = FastAPI(title="CI/CD Pipeline Demo")


@app.get("/health")
def health():
    return {"status": "ok"}
