import asyncio
import grpc
from bson import ObjectId

import grpc_generated.market_pb2 as market_pb2
import grpc_generated.market_pb2_grpc as market_pb2_grpc
# from db.mongo import connect_to_mongo

# class MarketService(market_pb2_grpc.MarketServiceServicer):
#     def __init__(self, db):
#         self.db = db
#         print("registered db ", self.db)

#     async def CreateMarket(self, request, context):
#         result = await self.db["markets"].insert_one({
#             "address": request.address,
#             "detail": request.detail
#         })
#         doc = await self.db["markets"].find_one({"_id": result.inserted_id})
#         return market_pb2.Market(
#             id=str(doc["_id"]),
#             address=doc["address"],
#             detail=doc.get("detail", "")
#         )

#     async def GetMarket(self, request, context):
#         try:
#             oid = ObjectId(request.id)
#         except Exception:
#             context.set_code(grpc.StatusCode.NOT_FOUND)
#             context.set_details("Invalid ID")
#             return market_pb2.Market()
#         doc = await self.db["markets"].find_one({"_id": oid})
#         if not doc:
#             context.set_code(grpc.StatusCode.NOT_FOUND)
#             context.set_details("Item not found")
#             return market_pb2.Market()
#         return market_pb2.Market(
#             id=str(doc["_id"]),
#             address=doc["address"],
#             detail=doc.get("detail", "")
#         )

#     async def GetAllMarket(self, request, context):
#         markets = []
#         async for doc in self.db["markets"].find():
#             markets.append(market_pb2.Market(
#                 id=str(doc["_id"]),
#                 address=doc.get("address", ""),
#                 detail=doc.get("detail", "")
#             ))
#         return market_pb2.MarketList(markets=markets)

#     async def UpdateMarket(self, request, context):
#         try:
#             oid = ObjectId(request.id)
#         except Exception:
#             context.set_code(grpc.StatusCode.NOT_FOUND)
#             context.set_details("Invalid ID")
#             return market_pb2.Market()
#         result = await self.db["markets"].update_one(
#             {"_id": oid},
#             {"$set": {"address": request.address, "detail": request.detail}}
#         )
#         if result.matched_count == 0:
#             context.set_code(grpc.StatusCode.NOT_FOUND)
#             context.set_details("Item not found")
#             return market_pb2.Market()
#         doc = await self.db["markets"].find_one({"_id": oid})
#         return market_pb2.Market(
#             id=str(doc["_id"]),
#             address=doc["address"],
#             detail=doc.get("detail", "")
#         )

#     async def DeleteMarket(self, request, context):
#         try:
#             oid = ObjectId(request.id)
#         except Exception:
#             context.set_code(grpc.StatusCode.NOT_FOUND)
#             context.set_details("Invalid ID")
#             return market_pb2.Empty()
#         result = await self.db["markets"].delete_one({"_id": oid})
#         if result.deleted_count == 0:
#             context.set_code(grpc.StatusCode.NOT_FOUND)
#             context.set_details("Item not found")
#         return market_pb2.Empty()

def MakeMarket(created):
     
    return market_pb2.Market(
        id=str(created.get("_id", "")) if created.get("_id", "") else "",
        market_name=created.get("market_name", ""),
        address=created.get("address", ""),
        cover_image_key=created.get("cover_image_key", ""),
        market_plan_keys=[
            market_pb2.MarketPlan(market_plan_key=mp.get("market_plan_key", ""))
            for mp in (created.get("market_plan_keys") or [])
        ],
        logs=[
            market_pb2.Log(
                name=lg.get("name", "NaN"),
                size=lg.get("size", ""),
                price=float(lg.get("price", 0.0)),
                user_id=lg.get("user_id", ""),
                reservation_id=lg.get("reservation_id", "")
            )
            for lg in (created.get("logs") or [])
        ],
        detail=created.get("detail", ""),
        rule=created.get("rule", ""),
        user_id=created.get("user_id", ""),
        isOpen=created.get("isOpen", False),
        marketType=created.get("marketType", "Market"),
    )

class MarketService(market_pb2_grpc.MarketServiceServicer):
    def __init__(self, db):
        self.db = db
        print("registered db ", self.db)

    # ---------- Create ----------
    async def CreateMarket(self, request, context):
        # store with snake_case keys to match proto fields
        doc = {
            "market_name": request.market_name or "",
            "address": request.address or "",
            "cover_image_key": request.cover_image_key or "",
            "market_plan_keys": [
                {"market_plan_key": mp.market_plan_key}
                for mp in request.market_plan_keys
            ],
            "logs": [
                {
                    "name": lg.name,
                    "size": lg.size,
                    "price": float(lg.price),
                    "user_id": lg.user_id,
                    "reservation_id": lg.reservation_id,
                }
                for lg in request.logs
            ],
            "detail": request.detail or "",
            "rule": request.rule or "",
            "user_id": request.user_id or "",
        }
        result = await self.db["markets"].insert_one(doc)
        created = await self.db["markets"].find_one({"_id": result.inserted_id})
        return MakeMarket(created)

    # ---------- Get one ----------
    async def GetMarket(self, request, context):
        try:
            oid = ObjectId(request.id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid ID")
            return market_pb2.Market()
        
        print("get2")
        doc = await self.db["markets"].find_one({"_id": oid})
        if not doc:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Market not found")
            return market_pb2.Market()

        return MakeMarket(doc)

    # ---------- List all ----------
    async def GetAllMarket(self, request, context):
        markets = []
        async for doc in self.db["markets"].find():
            markets.append(
                MakeMarket(doc)
            )
        
        return market_pb2.MarketList(markets=markets)

    # ---------- Get by User ID ----------
    async def GetMarketByUserID(self, request, context):
        markets = []
        async for doc in self.db["markets"].find({"user_id": request.user_id}):
            markets.append(
                MakeMarket(doc)
            )
        return market_pb2.MarketList(markets=markets)

    # ---------- Search Markets ----------
    async def SearchMarkets(self, request, context):
        # Build MongoDB query with OR logic
        or_conditions = []
        
        # General search query (searches across multiple fields)
        if request.query:
            or_conditions.extend([
                {"market_name": {"$regex": request.query, "$options": "i"}},
                {"address": {"$regex": request.query, "$options": "i"}},
                {"detail": {"$regex": request.query, "$options": "i"}},
                {"rule": {"$regex": request.query, "$options": "i"}}
            ])
        
        # Specific field searches (also use OR logic)
        if request.market_name:
            or_conditions.append({"market_name": {"$regex": request.market_name, "$options": "i"}})
        
        if request.address:
            or_conditions.append({"address": {"$regex": request.address, "$options": "i"}})
        
        if request.detail:
            or_conditions.append({"detail": {"$regex": request.detail, "$options": "i"}})
        
        # Build final query - fix recursion issue
        query = {}
        
        # Add OR conditions
        if or_conditions:
            query["$or"] = or_conditions
        
        # Add user_id filter
        if request.user_id:
            query["user_id"] = request.user_id
        
        # Set pagination defaults
        limit = request.limit if request.limit > 0 else 50
        offset = request.offset if request.offset >= 0 else 0
        
        # Get total count for pagination
        total_count = await self.db["markets"].count_documents(query)
        
        # Execute search with pagination
        markets = []
        async for doc in self.db["markets"].find(query).skip(offset).limit(limit):
            markets.append(
                MakeMarket(doc)
            )
        
        return market_pb2.SearchMarketsResponse(
            markets=markets,
            total_count=total_count,
            limit=limit,
            offset=offset
        )

    # ---------- Update (full replace via $set) ----------
    async def UpdateMarket(self, request, context):
        try:
            oid = ObjectId(request.id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid ID")
            return market_pb2.Market()

        new_data = {
            "market_name": request.market_name or "",
            "address": request.address or "",
            "cover_image_key": request.cover_image_key or "",
            "market_plan_keys": [
                {"market_plan_key": mp.market_plan_key}
                for mp in request.market_plan_keys
            ],
            "logs": [
                {
                    "name": lg.name,
                    "size": lg.size,
                    "price": float(lg.price),
                    "user_id": lg.user_id,
                    "reservation_id": lg.reservation_id,
                }
                for lg in request.logs
            ],
            "detail": request.detail or "",
            "rule": request.rule or "",
            "user_id": request.user_id or "",
            "isOpen": request.isOpen or False,
            "marketType": request.marketType or "Market"
        }

        result = await self.db["markets"].update_one({"_id": oid}, {"$set": new_data})
        if result.matched_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Market not found")
            return market_pb2.Market()

        doc = await self.db["markets"].find_one({"_id": oid})
        return MakeMarket(doc)

    # ---------- Delete ----------
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
            context.set_details("Market not found")
        return market_pb2.Empty()

# async def serve():
#     db = await connect_to_mongo()  # important!

#     if db == None : 
#         print("Can't connect with data base!")
#         return
    
#     server = grpc.aio.server()
#     market_pb2_grpc.add_MarketServiceServicer_to_server(MarketService(db), server)
#     server.add_insecure_port("[::]:50051") 
#     await server.start()
#     print("gRPC server running on port 50051")
#     await server.wait_for_termination()

# if __name__ == "__main__":
#     asyncio.run(serve())