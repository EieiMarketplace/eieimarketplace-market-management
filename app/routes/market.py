# app/routes/market.py
import json
from fastapi import  APIRouter, Form, UploadFile, File, HTTPException, Depends
from typing import List, Optional
import grpc
import uuid

from cloud.cloud import delete_with_image_key, get_presigned_url, upload_file_to_s3, validate_images_exist
from models.market import Market, MarketSearchResponse 
import grpc_generated.market_pb2 as market_pb2
import grpc_generated.market_pb2_grpc as market_pb2_grpc
from auth.auth import require_organizer_auth, UserInfo

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
                name= lg.name,
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
        isOpen=(m.isOpen or False),
        marketType=(m.marketType or "Market")
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
                "name": lg.name,
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
        isOpen=pm.isOpen,
        marketType=pm.marketType
    )


def grpc_not_found_to_404(e: grpc.aio.AioRpcError):
    if e.code() == grpc.StatusCode.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Market not found")
    elif e.code() == grpc.StatusCode.UNAUTHENTICATED:
        raise HTTPException(status_code=401, detail="Authentication required")
    elif e.code() == grpc.StatusCode.PERMISSION_DENIED:
        raise HTTPException(status_code=403, detail="Permission denied")
    raise e


# -------- Routes --------

# Create (Protected - Requires organizer authentication)
@router.post("/", response_model=Market, response_model_by_alias=True)
async def create_market(
    marketName: str = Form(...),
    address: str = Form(...),
    coverImageFile: Optional[UploadFile] = File(None),
    coverImageKey: Optional[str] = Form(None),
    marketPlanImageFiles: Optional[List[UploadFile]] = File(None),
    logs: Optional[str] = Form("[]"),
    detail: Optional[str] = Form(None),
    rule: Optional[str] = Form(None),
    isOpen: bool = Form(None),
    marketType: str = Form(None),
    user_info: UserInfo = Depends(require_organizer_auth)  # Auth check
):
 
    if coverImageFile:
        if not coverImageFile.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed.")

        try:
            file_extension = coverImageFile.filename.split(".")[-1].lower()
            s3_filename = f"{uuid.uuid4()}.{file_extension}"
            upload_file_to_s3(coverImageFile.file, s3_filename, coverImageFile.content_type)
            coverImageKey = s3_filename
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Handle market plan image files
    market_plan_keys = []
    if marketPlanImageFiles:
        for plan_file in marketPlanImageFiles:
            if not plan_file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Only image files are allowed for market plan images.")
         
            try:
                file_extension = plan_file.filename.split(".")[-1].lower()
                s3_filename = f"{uuid.uuid4()}.{file_extension}"
                upload_file_to_s3(plan_file.file, s3_filename, plan_file.content_type)
                market_plan_keys.append({"marketPlanKey": s3_filename})
            except RuntimeError as e:
                raise HTTPException(status_code=500, detail=str(e))
        
    try:
        logs_data = json.loads(logs)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in marketPlanKeys or logs")
    
    
    market = Market(
        id= "1",
        market_name=marketName,
        address=address,
        cover_image_key=coverImageKey,
        market_plan_keys=market_plan_keys,
        logs=logs_data,
        detail=detail,
        rule=rule,
        user_id=user_info.user_id,  # Use authenticated user's ID
        isOpen=isOpen,
        marketType=marketType
    )
 
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        # Server may generate id if empty
        req = to_proto_market(market)
        
        # Add authorization metadata for gRPC call
        metadata = [('authorization', f'Bearer {user_info.token}')]
        
        try:
            resp = await stub.CreateMarket(req, metadata=metadata)
        except grpc.aio.AioRpcError as e:
            raise grpc_not_found_to_404(e)
        return from_proto_market(resp)

# List all (Public - no auth required)
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
# @router.get(
#     "/user/{user_id}",
#     response_model=List[Market],
#     response_model_by_alias=True,
# )
# async def get_markets_by_user_id(user_id: str):
#     async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
#         stub = market_pb2_grpc.MarketServiceStub(channel)
#         resp = await stub.GetMarketByUserID(market_pb2.UserId(user_id=user_id))
#         return [from_proto_market(m) for m in resp.markets]

# Search markets (Public - no auth required)
@router.get(
    "/search",
    response_model=MarketSearchResponse,
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
        print("Check Rsppppppppppppppppppppppppppp",resp)
        market_list_res=[]
        for market_proto in resp.markets:
            market_res=from_proto_market(market_proto)
            if(market_res.cover_image_key!="" ):
                market_res.cover_image_url= get_presigned_url(market_res.cover_image_key)
            
            # Generate presigned URLs for market plan images
            if market_res.market_plan_keys:
                for plan in market_res.market_plan_keys:
                    if plan.market_plan_key:
                        plan.market_plan_image_url = get_presigned_url(plan.market_plan_key)
            
            market_list_res.append(market_res)
           
        return MarketSearchResponse(market=market_list_res,limit=resp.limit,total_count=resp.total_count)

# Get one (Public - no auth required)
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
            market_res= from_proto_market(resp)
            if(market_res.cover_image_key!="" ):
                market_res.cover_image_url=get_presigned_url(market_res.cover_image_key)
            
            # Generate presigned URLs for market plan images
            if market_res.market_plan_keys:
                for plan in market_res.market_plan_keys:
                    if plan.market_plan_key:
                        plan.market_plan_image_url = get_presigned_url(plan.market_plan_key)
            
            return market_res  
        except grpc.aio.AioRpcError as e:
            raise grpc_not_found_to_404(e)

# Update (Protected - Requires organizer authentication)
@router.put(
    "/{market_id}",
    response_model=Market,
    response_model_by_alias=True,
)
async def update_market(
    market_id: str,  
    marketName: str = Form(...),
    address: str = Form(...),
    coverImageKey: Optional[str] = Form(None),
    coverImageFile: Optional[UploadFile] = File(None),
    logs: Optional[str] = Form("[]"),
    marketPlanKeys:Optional[str]=Form(None),
    marketPlanImageFiles:Optional[List[UploadFile]] = File(None),  
    deletedMarketKeys: Optional[str] = Form(None),  
    detail: Optional[str] = Form(None),
    rule: Optional[str] = Form(None),
    isOpen: bool = Form(None),
    marketType: str = Form(None),
    user_info: UserInfo = Depends(require_organizer_auth)  # Auth check
):
    #IF cover image change
    #ADD new Image Key
    if coverImageFile:     
        #IF have old cover image will delete
        if coverImageKey!="" and validate_images_exist(coverImageKey):
            delete_with_image_key(coverImageKey)
        
        if not coverImageFile.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed.")

        try:
            file_extension = coverImageFile.filename.split(".")[-1].lower()
            s3_filename = f"{uuid.uuid4()}.{file_extension}"
            upload_file_to_s3(coverImageFile.file, s3_filename, coverImageFile.content_type)
            coverImageKey = s3_filename
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    #Change String to Json
    print("plan key", marketPlanKeys)
    print("deletedKey", deletedMarketKeys)
    try:
        allMarketPlanKeys = json.loads(marketPlanKeys) if marketPlanKeys else []
        deletedMarketKeys = json.loads(deletedMarketKeys) if deletedMarketKeys else []
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in marketPlanKeys or deletedMarketKeys")
    
    #Edit Market Plan
    #Delete Old Market And Collect Remain Key
    remain_market_plan_keys = [{"marketPlanKey": key} for key in allMarketPlanKeys if key not in deletedMarketKeys]
    for image_key in deletedMarketKeys:
        delete_with_image_key(image_key)
           
    # Handle market plan image files
    if marketPlanImageFiles:
        for plan_file in marketPlanImageFiles:
            if not plan_file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Only image files are allowed for market plan images.")
            try:
                file_extension = plan_file.filename.split(".")[-1].lower()
                s3_filename = f"{uuid.uuid4()}.{file_extension}"
                upload_file_to_s3(plan_file.file, s3_filename, plan_file.content_type)
                remain_market_plan_keys.append({"marketPlanKey": s3_filename})
            except RuntimeError as e:
                raise HTTPException(status_code=500, detail=str(e))
            
    #adjust log
    try:
        logs_data = json.loads(logs or "[]")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in logs")
    print(marketPlanImageFiles, remain_market_plan_keys)
 
        
    market = Market(
            id= market_id,
            market_name=marketName,
            address=address,
            cover_image_key=coverImageKey,
            market_plan_keys=remain_market_plan_keys,
            logs=logs_data,
            detail=detail,
            rule=rule,
            user_id=user_info.user_id,  # Use authenticated user's ID
            isOpen=isOpen,
            marketType=marketType
    )
  
    
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        # enforce path id
        m = market.model_copy(update={"id": market_id})
        
        # Add authorization metadata for gRPC call
        metadata = [('authorization', f'Bearer {user_info.token}')]
        
        try:
            resp = await stub.UpdateMarket(to_proto_market(m), metadata=metadata)
            return from_proto_market(resp)
        except grpc.aio.AioRpcError as e:
            raise grpc_not_found_to_404(e)

# Delete (Protected - Requires organizer authentication)
@router.delete("/{market_id}")
async def delete_market(
    market_id: str,
    user_info: UserInfo = Depends(require_organizer_auth)  # Auth check
):
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = market_pb2_grpc.MarketServiceStub(channel)
        
        # Add authorization metadata for gRPC call
        metadata = [('authorization', f'Bearer {user_info.token}')]
        
        try:
            await stub.DeleteMarket(market_pb2.MarketId(id=market_id), metadata=metadata)
            return {"detail": "Deleted successfully"}
        except grpc.aio.AioRpcError as e:
            raise grpc_not_found_to_404(e)


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")

    try:
        file_extension = file.filename.split(".")[-1].lower()
        s3_filename = f"{uuid.uuid4()}.{file_filename}"
 
        content_type = file.content_type   

        image= upload_file_to_s3(file.file, s3_filename, content_type)
        image_url = get_presigned_url(s3_filename)
        return {"message": "Image uploaded successfully", "image_url": image_url}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/images/{image_key}")
async def delete_image_from_s3(image_key: str):
    """
    Deletes an image from the specified S3 bucket.
    """
    try:
        delete_with_image_key(image_key)
        return {"message": "delete successfully"}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Test authentication endpoint
@router.get("/auth/test")
async def test_auth(user_info: UserInfo = Depends(require_organizer_auth)):
    """Test endpoint to verify authentication is working"""
    return {
        "message": "Authentication successful!",
        "user_id": user_info.user_id,
        "role": user_info.role,
        "authenticated": True
    }