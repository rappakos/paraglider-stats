import sys

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
import uvicorn

from glider_stats_app.routes import setup_routes
from glider_stats_app.middlewares import setup_middlewares
from glider_stats_app.db import setup_db

from config import DefaultConfig


CONFIG = DefaultConfig()


def create_app():
    app = FastAPI(root_path=CONFIG.ROOT_PATH)
    
    app.state.config = CONFIG
    app.state.templates = Jinja2Templates(directory="glider_stats_app/templates")
    
    # setup routes
    setup_routes(app)
    
    # setup middleware/exception handlers
    setup_middlewares(app)
    
    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    await setup_db(app)


def main(argv):
    uvicorn.run(
        "app:app",
        host='localhost',
        port=CONFIG.PORT,
        reload=True
    )


if __name__ == '__main__':
    main(sys.argv[1:])