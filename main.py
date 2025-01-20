from flask import Flask, request, jsonify
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
from enum import Enum
from pydantic import BaseModel, ValidationError
import asyncio

# Load environment variables
if os.getenv("ENVIRONMENT") == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env")

# MongoDB connection details
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "email_tracker_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "emails")

# Define valid tenants
class TenantEnum(str, Enum):
    AADVANTO = "aadvanto"
    MOVIDO = "movido"

# Define validation model
class EmailTrackRequest(BaseModel):
    customer_number: str
    tenant: TenantEnum

# Initialize Flask app
app = Flask(__name__)

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]

def run_async(coro):
    """Helper function to run async code in Flask"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route("/track-email")
def track_email():
    try:
        # Validate request data
        try:
            data = EmailTrackRequest(
                customer_number=request.args.get('customer_number'),
                tenant=request.args.get('tenant')
            )
        except ValidationError as e:
            return jsonify({
                "message": "Validation error",
                "errors": e.errors()
            }), 400

        async def process_request():
            try:
                # Verify database connection
                await client.admin.command('ping')
            except Exception as e:
                return {
                    "message": "Database connection failed",
                    "errors": str(e)
                }, 500

            # Try to find existing record
            existing_record = await collection.find_one({
                "customer_number": data.customer_number,
                "tenant": data.tenant
            })

            if existing_record:
                result = await collection.update_one(
                    {"_id": existing_record["_id"]},
                    {
                        "$inc": {"count": 1},
                        "$set": {
                            "timestamp": datetime.utcnow(),
                            "tenant": data.tenant
                        }
                    }
                )
                if result.modified_count:
                    return {"message": "Email tracking data updated successfully!"}, 200
            else:
                email_data = {
                    "customer_number": data.customer_number,
                    "tenant": data.tenant,
                    "timestamp": datetime.utcnow(),
                    "count": 1
                }
                result = await collection.insert_one(email_data)
                if result.inserted_id:
                    return {"message": "Email tracking data saved successfully!"}, 200

            return {"message": "Failed to save email tracking data"}, 500

        response, status_code = run_async(process_request())
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({
            "message": "Unknown Error",
            "errors": str(e)
        }), 500

@app.route("/")
def read_root():
    return jsonify({"message": "Welcome to the Email Tracker API v2.4.5!"})

# For vercel
app = apppip3 install --no-cache-dir -r requirements.txt