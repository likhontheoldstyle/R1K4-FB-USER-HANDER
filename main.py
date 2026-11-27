import uvicorn

from app.config import HOST, PORT
from app.routes import app

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
