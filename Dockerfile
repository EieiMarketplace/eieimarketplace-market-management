# Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install system deps (optional)
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files and app code
COPY app/protos ./protos
COPY app/grpc_generated ./grpc_generated
COPY app/ ./ 

# Generate gRPC Python code
# RUN python -m grpc_tools.protoc \
#     -I=protos \
#     --python_out=grpc_generated  \
#     --grpc_python_out=grpc_generated  \
#     protos/market.proto

# Use uvicorn; in production consider gunicorn + uvicorn workers
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7002"]

# Expose FastAPI and gRPC ports
EXPOSE 7002 50051

# Start FastAPI + gRPC together
# CMD ["python", "main.py"]
CMD ["bash", "-c", "cd grpc_generated && ls && cd .. && python main.py"]
