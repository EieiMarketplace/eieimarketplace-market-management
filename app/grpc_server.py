# app/grpc_server.py (snippet)
import asyncio
import grpc
# from .grpc_generated import market_pb2_grpc
from grpc_generated import market_pb2_grpc
from grpc_server_marketplan import MarketPlanService
from grpc_server_log import LogService
from grpc_server_market import MarketService
from db.mongo import connect_to_mongo

# async def serve(db, host: str = "0.0.0.0", port: int = 50051):
#     db = await connect_to_mongo()  # important!

#     if db == None : 
#         print("Can't connect with data base!")
#         return
#     server = grpc.aio.server()
#     market_pb2_grpc.add_MarketServiceServicer_to_server(MarketService(db), server)
#     market_pb2_grpc.add_MarketPlanServiceServicer_to_server(MarketPlanService(db), server)
#     market_pb2_grpc.add_LogServiceServicer_to_server(LogService(db), server)
#     server.add_insecure_port(f"{host}:{port}")
#     await server.start()
#     print(f"[gRPC] listening on {host}:{port}", flush=True)
#     await server.wait_for_termination()


async def serve():
    db = await connect_to_mongo()  # important!

    if db == None : 
        print("Can't connect with data base!")
        return
    
    server = grpc.aio.server()
    market_pb2_grpc.add_MarketServiceServicer_to_server(MarketService(db), server)
    market_pb2_grpc.add_MarketPlanServiceServicer_to_server(MarketPlanService(db), server)
    market_pb2_grpc.add_LogServiceServicer_to_server(LogService(db), server)
    server.add_insecure_port("[::]:50051") 
    await server.start()
    print("gRPC server running on port 50051")
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())