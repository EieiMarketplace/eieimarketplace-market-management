# app/grpc_server_marketplan.py
import grpc
from bson import ObjectId

import grpc_generated.market_pb2 as market_pb2
import grpc_generated.market_pb2_grpc as market_pb2_grpc
from db.mongo import connect_to_mongo
from grpc_generated import market_pb2, market_pb2_grpc

class MarketPlanService(market_pb2_grpc.MarketPlanServiceServicer):
    def __init__(self, db):
        self.db = db
        print("registered db (MarketPlanService) ", self.db)

    # ---------- Create ----------
    async def CreateMarketPlan(self, request, context):
        try:
            oid = ObjectId(request.market_id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid market ID")
            return market_pb2.MarketPlan()

        plan_doc = {"market_plan_key": request.plan.market_plan_key}
        # prevent duplicates by key
        result = await self.db["markets"].update_one(
            {"_id": oid},
            {"$addToSet": {"market_plan_keys": plan_doc}}
        )
        if result.matched_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Market not found")
            return market_pb2.MarketPlan()

        return market_pb2.MarketPlan(market_plan_key=request.plan.market_plan_key)

    # ---------- Get one ----------
    async def GetMarketPlan(self, request, context):
        try:
            oid = ObjectId(request.market_id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid market ID")
            return market_pb2.MarketPlan()

        doc = await self.db["markets"].find_one(
            {"_id": oid},
            {"market_plan_keys": {"$elemMatch": {"market_plan_key": request.market_plan_key}}}
        )
        plans = (doc or {}).get("market_plan_keys") or []
        if not plans:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("MarketPlan not found")
            return market_pb2.MarketPlan()

        return market_pb2.MarketPlan(market_plan_key=plans[0].get("market_plan_key", ""))

    # ---------- List ----------
    async def ListMarketPlans(self, request, context):
        try:
            oid = ObjectId(request.id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid market ID")
            return market_pb2.MarketPlanList()

        doc = await self.db["markets"].find_one({"_id": oid}, {"market_plan_keys": 1})
        plans = [
            market_pb2.MarketPlan(market_plan_key=p.get("market_plan_key", ""))
            for p in (doc or {}).get("market_plan_keys") or []
        ]
        return market_pb2.MarketPlanList(plans=plans)

    # ---------- Update (rename key) ----------
    async def UpdateMarketPlan(self, request, context):
        try:
            oid = ObjectId(request.market_id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid market ID")
            return market_pb2.MarketPlan()

        result = await self.db["markets"].update_one(
            {"_id": oid, "market_plan_keys.market_plan_key": request.old_key},
            {"$set": {"market_plan_keys.$.market_plan_key": request.new_key}}
        )
        if result.matched_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("MarketPlan not found")
            return market_pb2.MarketPlan()

        return market_pb2.MarketPlan(market_plan_key=request.new_key)

    # ---------- Delete ----------
    async def DeleteMarketPlan(self, request, context):
        try:
            oid = ObjectId(request.market_id)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Invalid market ID")
            return market_pb2.Empty()

        result = await self.db["markets"].update_one(
            {"_id": oid},
            {"$pull": {"market_plan_keys": {"market_plan_key": request.market_plan_key}}}
        )
        if result.matched_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Market not found")
        return market_pb2.Empty()
