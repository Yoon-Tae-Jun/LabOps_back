from fastapi import FastAPI
from contextlib import asynccontextmanager
from .db import init_db
from .auth.routes import auth_router
from .eagle.fastEx import eagle_router
from fastapi.middleware.cors import CORSMiddleware
import logging

@asynccontextmanager
async def life_span(app:FastAPI):
    print(f"Server is stating ...")
    await init_db()
    yield
    print(f"server has been stopped")

version = "v2"

app = FastAPI(
    title="JWT Authentication",
    description="Authentication using JWT",
    version=version,
    lifespan=life_span
)

logging.basicConfig(filename='info.log', level=logging.DEBUG)

def log_info(req_body, res_body):
    logging.info(req_body)
    logging.info(res_body)
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=f"/auth", tags=['auth'])
app.include_router(eagle_router, tags=['eagle'])
