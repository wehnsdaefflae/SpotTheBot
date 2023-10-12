from controller import Controller
import uvicorn

if __name__ == "__main__":
    controller = Controller()
    uvicorn.run("view:app", host="0.0.0.0", port=8000, reload=True)
