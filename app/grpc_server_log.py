# app/grpc_server_log.py
import grpc
from bson import ObjectId

import grpc_generated.market_pb2 as market_pb2
import grpc_generated.market_pb2_grpc as market_pb2_grpc
from db.mongo import connect_to_mongo
from grpc_generated import market_pb2, market_pb2_grpc

def MakeLog(lg):
    return market_pb2.Log(
        name=lg.get("name", "NaN"),
        size=lg.get("size", ""),
        price=float(lg.get("price", 0.0)),
        user_id=int(lg.get("user_id", 0)),
        reservation_id=int(lg.get("reservation_id", 0)),
    )

class LogService(market_pb2_grpc.LogServiceServicer):
    def __init__(self, db):
        self.db = db
        print("registered db (LogService) ", self.db)
    
    # ---------- Create ----------
    async def CreateLog(self, request, context):
        try:
            oid = ObjectId(request.market_id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid market ID")
            return market_pb2.Log()

        # uniqueness: reservation_id within a market
        exists = await self.db["markets"].find_one(
            {"_id": oid, "logs.reservation_id": request.log.reservation_id},
            {"_id": 1}
        )
        if exists:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("Log with this reservation_id already exists")
            return market_pb2.Log()

        log_doc = {
            "name": request.log.name,
            "size": request.log.size,
            "price": float(request.log.price),
            "user_id": int(request.log.user_id),
            "reservation_id": int(request.log.reservation_id),
        }
        result = await self.db["markets"].update_one(
            {"_id": oid},
            {"$push": {"logs": log_doc}}
        )
        if result.matched_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Market not found")
            return market_pb2.Log()

        return MakeLog(request.log)
        #return market_pb2.Log(**log_doc)

    # ---------- Get one ----------
    async def GetLog(self, request, context):
        try:
            oid = ObjectId(request.market_id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid market ID")
            return market_pb2.Log()

        doc = await self.db["markets"].find_one(
            {"_id": oid},
            {"logs": {"$elemMatch": {"reservation_id": int(request.reservation_id)}}}
        )
        logs = (doc or {}).get("logs") or []
        if not logs:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Log not found")
            return market_pb2.Log()

        lg = logs[0]
        return MakeLog(lg)

    # ---------- List ----------
    async def ListLogs(self, request, context):
        try:
            oid = ObjectId(request.id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid market ID")
            return market_pb2.LogList()

        doc = await self.db["markets"].find_one({"_id": oid}, {"logs": 1})
        logs = [
            MakeLog(lg) for lg in (doc or {}).get("logs") or []
        ]
        return market_pb2.LogList(logs=logs)

    # ---------- Update ----------
    async def UpdateLog(self, request, context):
        try:
            oid = ObjectId(request.market_id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid market ID")
            return market_pb2.Log()

        # update by reservation_id
        result = await self.db["markets"].update_one(
            {"_id": oid, "logs.reservation_id": int(request.log.reservation_id)},
            {"$set": {
                "logs.$.size": request.log.size,
                "logs.$.price": float(request.log.price),
                "logs.$.user_id": int(request.log.user_id),
                # reservation_id remains the identifier; can still be set to same value
                "logs.$.reservation_id": int(request.log.reservation_id),
            }}
        )
        if result.matched_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Log not found")
            return market_pb2.Log()

        # return updated log
        doc = await self.db["markets"].find_one(
            {"_id": oid},
            {"logs": {"$elemMatch": {"reservation_id": int(request.log.reservation_id)}}}
        )
        lg = ((doc or {}).get("logs") or [{}])[0]
        return MakeLog(lg)

    # ---------- Delete ----------
    async def DeleteLog(self, request, context):
        try:
            oid = ObjectId(request.market_id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid market ID")
            return market_pb2.Empty()

        result = await self.db["markets"].update_one(
            {"_id": oid},
            {"$pull": {"logs": {"reservation_id": int(request.reservation_id)}}}
        )
        if result.matched_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Market not found")
        return market_pb2.Empty()
