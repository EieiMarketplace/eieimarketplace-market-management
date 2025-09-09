import asyncio
import grpc
from bson import ObjectId

import grpc_generated.market_pb2 as market_pb2
import grpc_generated.market_pb2_grpc as market_pb2_grpc
from db.mongo import connect_to_mongo

class MarketService(market_pb2_grpc.MarketServiceServicer):
    def __init__(self, db):
        self.db = db
        print("registered db ", self.db)

    async def CreateMarket(self, request, context):
        result = await self.db["markets"].insert_one({
            "address": request.address,
            "detail": request.detail
        })
        doc = await self.db["markets"].find_one({"_id": result.inserted_id})
        return market_pb2.Market(
            id=str(doc["_id"]),
            address=doc["address"],
            detail=doc.get("detail", "")
        )

    async def GetMarket(self, request, context):
        try:
            oid = ObjectId(request.id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid ID")
            return market_pb2.Market()
        doc = await self.db["markets"].find_one({"_id": oid})
        if not doc:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Item not found")
            return market_pb2.Market()
        return market_pb2.Market(
            id=str(doc["_id"]),
            address=doc["address"],
            detail=doc.get("detail", "")
        )

    async def GetAllMarket(self, request, context):
        markets = []
        async for doc in self.db["markets"].find():
            markets.append(market_pb2.Market(
                id=str(doc["_id"]),
                address=doc.get("address", ""),
                detail=doc.get("detail", "")
            ))
        return market_pb2.MarketList(markets=markets)

    async def UpdateMarket(self, request, context):
        try:
            oid = ObjectId(request.id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid ID")
            return market_pb2.Market()
        result = await self.db["markets"].update_one(
            {"_id": oid},
            {"$set": {"address": request.address, "detail": request.detail}}
        )
        if result.matched_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Item not found")
            return market_pb2.Market()
        doc = await self.db["markets"].find_one({"_id": oid})
        return market_pb2.Market(
            id=str(doc["_id"]),
            address=doc["address"],
            detail=doc.get("detail", "")
        )

    async def DeleteMarket(self, request, context):
        try:
            oid = ObjectId(request.id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid ID")
            return market_pb2.Empty()
        result = await self.db["markets"].delete_one({"_id": oid})
        if result.deleted_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Item not found")
        return market_pb2.Empty()


async def serve():
    db = await connect_to_mongo()  # important!

    if db == None : 
        print("Can't connect with data base!")
        return
    
    server = grpc.aio.server()
    market_pb2_grpc.add_MarketServiceServicer_to_server(MarketService(db), server)
    server.add_insecure_port("[::]:50051") 
    await server.start()
    print("gRPC server running on port 50051")
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())