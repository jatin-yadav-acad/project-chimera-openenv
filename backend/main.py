from fastapi import FastAPI

print("🔥 MAIN FILE LOADED")

app = FastAPI()

@app.get("/")
def root():
    return {"status": "alive"}