#!/usr/bin/env python3
import frontend
from fastapi import FastAPI

app = FastAPI()


frontend.init(app)

if __name__ == '__main__':
    print(
        "Please start the app with\n" +
        "`uvicorn main:app --reload --log-level debug --port 8000 --host 0.0.0.0`"
    )
