# Knowledge Base API

A FastAPI application for managing AWS Bedrock knowledge bases with three main functionalities:
- Uploading documents to S3
- Triggering ingestion jobs
- Querying the knowledge base

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Configure AWS credentials:
   - Open `app.py` and replace the placeholder values with your actual AWS credentials:
   ```python
   # Replace these with your actual credentials
   AWS_ACCESS_KEY_ID = "your_access_key_here"
   AWS_SECRET_ACCESS_KEY = "your_secret_key_here"
   ```
   - You can also update other configuration values if needed:
   ```python
   BUCKET_NAME = "joveo-data-lake-dev"
   KNOWLEDGE_BASE_ID = "0NFDU3JJEA"
   DATA_SOURCE_ID = "RLSHWA5C0H"
   AWS_REGION = "us-east-1"
   ```

3. Run the application:
```
uvicorn app:app --reload
```

## Environment Variables

The following environment variables can be configured in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| AWS_ACCESS_KEY_ID | Your AWS access key | - |
| AWS_SECRET_ACCESS_KEY | Your AWS secret key | - |
| AWS_REGION | AWS region | us-east-1 |
| BUCKET_NAME | S3 bucket name | joveo-data-lake-dev |
| KNOWLEDGE_BASE_ID | Bedrock knowledge base ID | 0NFDU3JJEA |
| DATA_SOURCE_ID | Bedrock data source ID | RLSHWA5C0H |
| MODEL_ARN | Bedrock model ARN | arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0 |

## API Endpoints

### 1. Upload a text file
**Endpoint**: POST /upload  
**Request**: Form data with a text file  
**Response**: S3 key and success message

Example using curl:
```
curl -X POST -F "file=@yourfile.txt" http://localhost:8000/upload
```

### 2. Trigger ingestion
**Endpoint**: POST /ingest  
**Response**: Ingestion job ID and status

Example using curl:
```
curl -X POST http://localhost:8000/ingest
```

You can check the status of an ingestion job with:
```
curl http://localhost:8000/ingest/{ingestion_job_id}
```

### 3. Query the knowledge base
**Endpoint**: POST /query  
**Request**: JSON with a text query  
**Response**: Response from the knowledge base

Example using curl:
```
curl -X POST -H "Content-Type: application/json" -d '{"text":"your query here"}' http://localhost:8000/query
```

## Interactive Documentation
Access the Swagger UI documentation at http://localhost:8000/docs 