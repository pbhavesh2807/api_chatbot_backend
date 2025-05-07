from fastapi import FastAPI, UploadFile, File, HTTPException
import boto3
import os
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Remove dotenv import and loading
# from dotenv import load_dotenv
# load_dotenv()

app = FastAPI(title="Knowledge Base API", description="API for managing and querying AWS Bedrock knowledge bases")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://api-chatbot-frontend.vercel.app"],  # Allows the React app running on port 3000
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Hard-coded configuration values instead of environment variables
BUCKET_NAME = "joveo-data-lake-dev"
KNOWLEDGE_BASE_ID = "0NFDU3JJEA"
DATA_SOURCE_ID = "RLSHWA5C0H"
AWS_REGION = "us-east-1"
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
AWS_ACCOUNT_ID = "997116068644"

# Initialize Boto3 clients
s3_client = boto3.client("s3", region_name=AWS_REGION)
bedrock_agent_client = boto3.client("bedrock-agent", region_name=AWS_REGION)
bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

# Models
class Query(BaseModel):
    text: str

class UploadResponse(BaseModel):
    s3_key: str
    message: str

class IngestResponse(BaseModel):
    ingestion_job_id: str
    status: str

@app.post("/upload", response_model=UploadResponse)
async def upload_to_s3(file: UploadFile = File(...)):
    """Upload a .txt file to S3"""
    try:
        # Ensure file is .txt
        if not file.filename.endswith(".txt"):
            raise HTTPException(status_code=400, detail="Only .txt files are supported")
        
        # Read file contentS
        file_content = await file.read()
        
        # Generate S3 key
        s3_key = f"publisher-kb/{file.filename}"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_content
        )
        
        return {"s3_key": s3_key, "message": f"File uploaded successfully to s3://{BUCKET_NAME}/{s3_key}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/ingest", response_model=IngestResponse)
def ingest_to_knowledge_base():
    """Trigger ingestion job to process S3 files and store embeddings"""
    try:
        # Start ingestion job
        start_job_response = bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            dataSourceId=DATA_SOURCE_ID
        )
        
        job = start_job_response["ingestionJob"]
        ingestion_job_id = job["ingestionJobId"]
        
        return {"ingestion_job_id": ingestion_job_id, "status": job["status"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during ingestion: {str(e)}")

@app.get("/ingest/{ingestion_job_id}")
def get_ingestion_status(ingestion_job_id: str):
    """Get the status of an ingestion job"""
    try:
        get_job_response = bedrock_agent_client.get_ingestion_job(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            dataSourceId=DATA_SOURCE_ID,
            ingestionJobId=ingestion_job_id
        )
        job = get_job_response["ingestionJob"]
        
        return {"ingestion_job_id": ingestion_job_id, "status": job["status"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ingestion status: {str(e)}")

@app.post("/query")
def query_knowledge_base(query: Query):
    """Query the knowledge base and return the response"""
    try:
        # Print detailed information for debugging
        print(f"Query text: {query.text}")
        print(f"KNOWLEDGE_BASE_ID: {KNOWLEDGE_BASE_ID}")
        
        # Call RetrieveAndGenerate API
        try:
            response = bedrock_agent_runtime_client.retrieve_and_generate(
                input={"text": query.text},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                        "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                    }
                }
            )
            
            print("Response received successfully")
            return {"response": response["output"]["text"]}
        except Exception as api_error:
            # Get detailed API error information
            print(f"API Error details: {str(api_error)}")
            
            # Check if it's an expired token or credentials issue
            error_str = str(api_error).lower()
            if "access denied" in error_str or "authentication" in error_str or "credential" in error_str:
                raise HTTPException(
                    status_code=401, 
                    detail="AWS credential error. Please check your AWS credentials."
                )
            # Check if it's a model ARN formatting issue
            elif "validation" in error_str and "modela" in error_str:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid model ARN format."
                )
            else:
                raise HTTPException(
                    status_code=500, 
                    detail={
                        "message": "Error calling Bedrock API",
                        "error": str(api_error)
                    }
                )
    except Exception as e:
        print(f"General error in query_knowledge_base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying knowledge base: {str(e)}")

@app.get("/")
def read_root():
    """Root endpoint to verify the API is running"""
    return {"message": "Knowledge Base API is running", "status": "online"}

# This is optional but helps with Vercel deployments
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 