# app/routes/market.py
from fastapi import APIRouter, HTTPException
from typing import List
import grpc

from models.market import Market  # <- Pydantic models from previous step
import grpc_generated.market_pb2 as market_pb2
import grpc_generated.market_pb2_grpc as market_pb2_grpc

router = APIRouter()
GRPC_SERVER = "localhost:50051"

# -------- Marshaling helpers (Pydantic <-> gRPC) --------

def to_proto_market(m: Market) -> market_pb2.Market:
    return market_pb2.Market(
        id=(m.id or ""),
        market_name=(m.market_name or ""),
        address=(m.address or ""),
        cover_image_key=(m.cover_image_key or ""),
        market_plan_keys=[
            market_pb2.MarketPlan(market_plan_key=mp.market_plan_key)
            for mp in (m.market_plan_keys or [])
        ],
        logs=[
            market_pb2.Log(
                size=lg.size,
                price=lg.price,
                user_id=lg.user_id,
                reservation_id=lg.reservation_id,
            )
            for lg in (m.logs or [])
        ],
        detail=(m.detail or ""),
        rule=(m.rule or ""),
        user_id=(m.user_id or ""),
    )


def from_proto_market(pm: market_pb2.Market) -> Market:
    return Market(
        id=pm.id,
        market_name=pm.market_name,
        address=pm.address,
        cover_image_key=pm.cover_image_key,
        market_plan_keys=[{"marketPlanKey": mp.market_plan_key} for mp in pm.market_plan_keys],
        logs=[
            {
                "size": lg.size,
                "price": lg.price,
                "userID": lg.user_id,
                "reservationID": lg.reservation_id,
            }
            for lg in pm.logs
        ],
        detail=pm.detail,
        rule=pm.rule,
        user_id=pm.user_id,
    )


def grpc_not_found_to_404(e: grpc.aio.AioRpcError):
    if e.code() == grpc.StatusCode.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Market not found")
    raise e


# -------- Routes --------

# Create
@router.post(
    "/",
    response_model=Market,
    response_model_by_alias=True,  # ensures camelCase in JSON
)
async def create_market(market: Market):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        # Server may generate id if empty
        req = to_proto_market(market)
        try:
            resp = await stub.CreateMarket(req)
        except grpc.aio.AioRpcError as e:
            raise grpc_not_found_to_404(e)
        return from_proto_market(resp)

# List all
@router.get(
    "/",
    response_model=List[Market],
    response_model_by_alias=True,
)
async def list_markets():
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        resp = await stub.GetAllMarket(market_pb2.Empty())
        return [from_proto_market(m) for m in resp.markets]

# Get markets by user ID
@router.get(
    "/user/{user_id}",
    response_model=List[Market],
    response_model_by_alias=True,
)
async def get_markets_by_user_id(user_id: str):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        resp = await stub.GetMarketByUserID(market_pb2.UserId(user_id=user_id))
        return [from_proto_market(m) for m in resp.markets]

# Search markets
@router.get(
    "/search",
    response_model=List[Market],
    response_model_by_alias=True,
)
async def search_markets(
    query: str = None,
    market_name: str = None,
    address: str = None,
    detail: str = None,
    user_id: str = None,
    limit: int = 50,
    offset: int = 0
):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        resp = await stub.SearchMarkets(
            market_pb2.SearchMarketsRequest(
                query=query or "",
                market_name=market_name or "",
                address=address or "",
                detail=detail or "",
                user_id=user_id or "",
                limit=limit,
                offset=offset
            )
        )
        return [from_proto_market(m) for m in resp.markets]

# Get one
@router.get(
    "/{market_id}",
    response_model=Market,
    response_model_by_alias=True,
)
async def get_market(market_id: str):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        try:
            resp = await stub.GetMarket(market_pb2.MarketId(id=market_id))
            return from_proto_market(resp)
        except grpc.aio.AioRpcError as e:
            raise grpc_not_found_to_404(e)

# Update (full replace semantics)
@router.put(
    "/{market_id}",
    response_model=Market,
    response_model_by_alias=True,
)
async def update_market(market_id: str, market: Market):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        # enforce path id
        m = market.model_copy(update={"id": market_id})
        try:
            resp = await stub.UpdateMarket(to_proto_market(m))
            return from_proto_market(resp)
        except grpc.aio.AioRpcError as e:
            raise grpc_not_found_to_404(e)

# Delete
@router.delete("/{market_id}")
async def delete_market(market_id: str):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        try:
            await stub.DeleteMarket(market_pb2.MarketId(id=market_id))
            return {"detail": "Deleted successfully"}
        except grpc.aio.AioRpcError as e:
            raise grpc_not_found_to_404(e)
