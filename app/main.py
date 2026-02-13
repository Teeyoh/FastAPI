from fastapi import FastAPI
import os

app = FastAPI(title="CI/CD Pipeline Demo")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"git_sha": os.getenv("GIT_SHA", "dev")}
