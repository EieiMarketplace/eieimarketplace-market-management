from fastapi import APIRouter, HTTPException
from typing import List
import grpc
import asyncio

from models.market import Market, MarketId
import grpc_generated.market_pb2 as market_pb2
import grpc_generated.market_pb2_grpc as market_pb2_grpc

router = APIRouter()

GRPC_SERVER = "localhost:50051"  # gRPC server address

async def get_grpc_channel():
    channel = grpc.aio.insecure_channel(GRPC_SERVER)
    try:
        yield channel
    finally:
        await channel.close()

# Create
@router.post("/", response_model=MarketId)
async def create_market(market: Market):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        response = await stub.CreateMarket(
            market_pb2.Market(address=market.address, detail=market.detail or "")
        )
        return MarketId(id=response.id, address=response.address, detail=response.detail)

# List all
@router.get("/", response_model=List[MarketId])
async def list_markets():
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        response = await stub.GetAllMarket(market_pb2.Empty())
        return [MarketId(id=i.id, address=i.address, detail=i.detail) for i in response.markets]

# Get one
@router.get("/{market_id}", response_model=MarketId)
async def get_market(market_id: str):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        try:
            response = await stub.GetMarket(market_pb2.MarketId(id=market_id))
            return MarketId(id=response.id, address=response.address, detail=response.detail)
        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise HTTPException(status_code=404, detail="Market not found")
            raise

# Update
@router.put("/{market_id}", response_model=MarketId)
async def update_market(market_id: str, market: Market):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        try:
            response = await stub.UpdateMarket(
                market_pb2.Market(id=market_id, address=market.address or "", detail=market.detail or "")
            )
            return Market(id=response.id, address=response.address, detail=response.detail)
        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise HTTPException(status_code=404, detail="Item not found")
            raise

# Delete
@router.delete("/{market_id}")
async def delete_item(market_id: str):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        try:
            await stub.DeleteMarket(market_pb2.MarketId(id=market_id))
            return {"detail": "Deleted successfully"}
        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise HTTPException(status_code=404, detail="Item not found")
            raise
