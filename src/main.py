from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
def root():
    return {'message': 'Hello World'}





@app.post('/provider/dingtalk/register/')
def callback():
    pass