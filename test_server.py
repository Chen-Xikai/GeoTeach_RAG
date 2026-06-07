from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    print("Starting simple server on http://127.0.0.1:9767")
    uvicorn.run(app, host="127.0.0.1", port=9767)
