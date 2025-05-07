import boto3
import base64
import json
import os
import time
from datetime import datetime

# Configuration
BUCKET_NAME = "joveo-data-lake-dev"  # Replace with your S3 bucket name
KNOWLEDGE_BASE_ID = "0NFDU3JJEA"  # Replace with your Knowledge Base ID
DATA_SOURCE_ID = "RLSHWA5C0H"  # Replace with your Data Source ID
AWS_REGION = "us-east-1"  # Replace with your AWS region
LOCAL_FILE_PATH = "../data/194e1f0305afd963.txt"

# Initialize Boto3 clients
s3_client = boto3.client("s3", region_name=AWS_REGION)
bedrock_agent_client = boto3.client("bedrock-agent", region_name=AWS_REGION)
bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)


def upload_to_s3(file_path):
    """Upload a .txt file to S3"""
    try:
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()

        file_name = os.path.basename(file_path)

        # Ensure file is .txt
        if not file_name.endswith(".txt"):
            raise ValueError("Only .txt files are supported")

        # Generate unique file key
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        s3_key = f"publisher-kb/{file_name}"

        # Upload to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_content
        )

        print(f"File uploaded successfully to s3://{BUCKET_NAME}/{s3_key}")
        return s3_key
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        raise


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
        print(f"Started ingestion job: {ingestion_job_id}")

        # Poll for job completion
        while job["status"] not in ["COMPLETE", "FAILED"]:
            get_job_response = bedrock_agent_client.get_ingestion_job(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                dataSourceId=DATA_SOURCE_ID,
                ingestionJobId=ingestion_job_id
            )
            job = get_job_response["ingestionJob"]
            print(f"Ingestion job status: {job['status']}")
            time.sleep(10)  # Wait before polling again

        if job["status"] == "COMPLETE":
            print("Ingestion job completed successfully")
        else:
            raise Exception(f"Ingestion job failed with status: {job['status']}")

        return job["status"]
    except Exception as e:
        print(f"Error during ingestion: {str(e)}")
        raise


def query_knowledge_base(query):
    """Query the knowledge base and return the response"""
    try:
        # Call RetrieveAndGenerate API
        response = bedrock_agent_runtime_client.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                }
            }
        )

        print("Query response:", response["output"]["text"])
        return response["output"]["text"]
    except Exception as e:
        print(f"Error querying knowledge base: {str(e)}")
        raise


def main():
    try:
        # Step 1: Upload file to S3
        s3_key = upload_to_s3(LOCAL_FILE_PATH)

        # Step 2: Trigger ingestion
        # ingest_to_knowledge_base()

        # Step 3: Query the knowledge base
        # time.sleep(30)  # Wait for ingestion to complete
        # query = "summarize the discussion with Adzuna publisher?"
        # query_knowledge_base(query)

    except Exception as e:
        print(f"Flow failed: {str(e)}")


if __name__ == "__main__":
    main()