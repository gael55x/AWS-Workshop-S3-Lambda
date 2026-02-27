import json
import uuid
import os
import boto3
from botocore.config import Config
import boto3

s3 = boto3.client(
    "s3",
    region_name="ap-southeast-1",
    endpoint_url="https://s3.ap-southeast-1.amazonaws.com",
    config=Config(signature_version="s3v4"),
)

def handler(event, context):
    method = (event.get("requestContext", {}).get("http", {}).get("method") or "").upper()
    
    # CORS headers required by browsers
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "content-type",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }
    
    if method == "OPTIONS":
        return {"statusCode": 204, "headers": headers, "body": ""}

    # REPLACE THIS with your actual S3 bucket name
    bucket = "private-amolong-123"

    # ROUTE 1: Upload an Image (POST)
    if method == "POST":
        body_raw = event.get("body") or "{}"
        try:
            body = json.loads(body_raw)
        except json.JSONDecodeError:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Invalid JSON body."})}

        filename = body.get("filename", "")
        content_type = body.get("contentType", "application/octet-stream")
        
        ext = ".jpg" if not filename or "." not in filename else "." + filename.rsplit(".", 1)[-1].lower()
        key = f"images/{uuid.uuid4().hex}{ext}"

        try:
            upload_url = s3.generate_presigned_url(
                ClientMethod="put_object",
                Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
                ExpiresIn=300,
            )
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"uploadUrl": upload_url, "key": key}),
            }
        except Exception as e:
            return {"statusCode": 500, "headers": headers, "body": json.dumps({"error": "Failed to generate presigned URL."})}

    # ROUTE 2: List all Images (GET)
    elif method == "GET":
        try:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix="images/", MaxKeys=24)
            contents = resp.get("Contents") or []
            
            filtered = []
            for obj in contents:
                key = obj.get("Key")
                if not key or key.endswith("/"):
                    continue
                lm = obj.get("LastModified") or datetime.min
                filtered.append((lm, key))
                
            filtered.sort(key=lambda x: x[0], reverse=True)
            keys = [k for _, k in filtered[:24]]
            
            image_urls = []
            for key in keys:
                url = s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=300, 
                )
                image_urls.append(url)
                
            return {
                "statusCode": 200, 
                "headers": headers, 
                "body": json.dumps({"images": image_urls})
            }
        except Exception as e:
            return {"statusCode": 500, "headers": headers, "body": json.dumps({"error": f"Failed to list images: {str(e)}"})}
            
    # Fallback response
    return {"statusCode": 405, "headers": headers, "body": json.dumps({"error": "Method Not Allowed"})}
