python -m grpc_tools.protoc ^
    -I=app/protos ^
    --python_out=app/grpc_generated ^
    --grpc_python_out=app/grpc_generated ^
    app/protos/market.proto
