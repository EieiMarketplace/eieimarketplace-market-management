import asyncio
from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager

from db.mongo import connect_to_mongo, close_mongo_connection
from routes import market
from grpc_server import serve as serve_grpc
from fastapi.middleware.cors import CORSMiddleware
 

app = FastAPI(title="Eiei Marketplace Market Management")

list = ["http://localhost:5000",
        "http://localhost:8000",
        "http://localhost:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000", "http://localhost:8000"],       
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],          
    allow_headers=["*"],          
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    close_mongo_connection()

app.include_router(market.router, prefix="/markets", tags=["Markets"])

async def serve_fastapi():
    config = uvicorn.Config(app, host="0.0.0.0", port=7002)
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await asyncio.gather(
        serve_fastapi(),
        serve_grpc()
    )

if __name__ == "__main__":
    asyncio.run(main())
