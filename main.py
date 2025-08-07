from fastapi import FastAPI, Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import hashlib
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Webhook API Service", version="1.0.0")

# MongoDB configuration from environment variables
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "webhook_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "webhook_requests")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# MongoDB client
client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]
collection = database[COLLECTION_NAME]


@app.on_event("startup")
async def startup_event():
    """Test MongoDB connection on startup"""
    try:
        await client.admin.command("ping")
        print(f"Connected to MongoDB at {MONGODB_URL}")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    client.close()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Webhook API Service is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check with database status"""
    try:
        await client.admin.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
)
async def catch_all_webhook(request: Request, path: str = ""):
    """
    Catch-all endpoint to handle webhook requests from any path
    Logs all request details to MongoDB
    """
    try:
        # Check token for webhook-with-token path
        if path == "webhook-with-token":
            x_signature = request.headers.get("x-signature")
            if not x_signature:
                raise HTTPException(
                    status_code=401,
                    detail="Missing X-Signature header for webhook-with-token endpoint",
                )

            # Generate expected signature
            secret_key = "asilla"
            expected_signature = hashlib.sha256(secret_key.encode()).hexdigest()

            # Compare signatures
            if x_signature != expected_signature:
                raise HTTPException(
                    status_code=401, detail="Invalid signature. Authentication failed."
                )

            print(f"Token validation successful for path: {path}")

        # Get request body
        body = None
        content_type = request.headers.get("content-type", "")

        if content_type.startswith("application/json"):
            try:
                body = await request.json()
            except Exception:
                body_bytes = await request.body()
                body = body_bytes.decode("utf-8") if body_bytes else None
        else:
            body_bytes = await request.body()
            body = body_bytes.decode("utf-8") if body_bytes else None

        # Prepare document to save
        webhook_data = {
            "timestamp": datetime.utcnow(),
            "method": request.method,
            "url": str(request.url),
            "path": f"/{path}" if path else "/",
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
            "body": body,
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "content_type": content_type,
            "content_length": request.headers.get("content-length"),
            "x_signature": request.headers.get("x-signature"),
            "x_timestamp": request.headers.get("x-timestamp"),
        }

        # Save to MongoDB
        result = await collection.insert_one(webhook_data)

        # Log to console
        print(f"Received {request.method} request to {request.url}")
        print(f"Headers: {dict(request.headers)}")
        if body:
            print(f"Body: {body}")
        print(f"Saved to MongoDB with ID: {result.inserted_id}")

        # Return success response
        return {
            "status": "success",
            "message": "Webhook received and logged",
            "timestamp": webhook_data["timestamp"].isoformat(),
            "method": request.method,
            "path": webhook_data["path"],
            "logged_id": str(result.inserted_id),
        }

    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@app.get("/logs")
async def get_logs(limit: int = 10, skip: int = 0):
    """
    Get recent webhook logs from MongoDB
    """
    try:
        cursor = collection.find().sort("timestamp", -1).skip(skip).limit(limit)
        logs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["timestamp"] = doc["timestamp"].isoformat()
            logs.append(doc)

        total_count = await collection.count_documents({})

        return {
            "logs": logs,
            "total_count": total_count,
            "returned_count": len(logs),
            "skip": skip,
            "limit": limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")


@app.get("/logs/count")
async def get_logs_count():
    """Get total count of logged requests"""
    try:
        count = await collection.count_documents({})
        return {"total_requests": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting logs: {str(e)}")


@app.delete("/logs")
async def clear_logs():
    """Clear all logs (use with caution)"""
    try:
        result = await collection.delete_many({})
        return {
            "status": "success",
            "message": f"Deleted {result.deleted_count} log entries",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing logs: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
