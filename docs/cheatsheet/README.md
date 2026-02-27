| Area | Command | What it does |
|---|---|---|
| Setup | `export AWS_REGION="ap-southeast-1"` | Sets the workshop region for CLI commands. |
| Setup | `export AWS_PROFILE="<your-profile>"` | (Optional) Selects an AWS CLI profile to use for all commands. |
| Setup | `export FRONTEND_BUCKET="my-cat-workshop-frontend-<initials>-<digits>"` | Sets your public website bucket name. |
| Setup | `export IMAGES_BUCKET="my-cat-workshop-images-<initials>-<digits>"` | Sets your private uploads bucket name. |
| Setup | `export FUNCTION_NAME="cat-upload-api"` | Sets the Lambda function name used in Lecture 2. |
| Auth | `aws --version` | Confirms AWS CLI is installed and shows its version. |
| Auth | `aws configure sso` | Creates/updates an AWS SSO-based CLI profile. |
| Auth | `aws sso login` | Logs in via AWS SSO for the default profile. |
| Auth | `aws sso login --profile "<profile-name>"` | Logs in via AWS SSO for a specific profile. |
| Auth | `aws sts get-caller-identity` | Shows the AWS account + principal you’re authenticated as (fastest “am I logged in?” check). |
| Auth | `aws configure get region` | Prints the CLI default region (if configured). |
| Auth | `aws configure set region "$AWS_REGION"` | Sets the CLI default region to `ap-southeast-1`. |
| S3 | `aws s3api create-bucket --bucket "$FRONTEND_BUCKET" --region "$AWS_REGION" --create-bucket-configuration LocationConstraint="$AWS_REGION"` | Creates the frontend bucket in the workshop region. |
| S3 | `aws s3api create-bucket --bucket "$IMAGES_BUCKET" --region "$AWS_REGION" --create-bucket-configuration LocationConstraint="$AWS_REGION"` | Creates the images bucket in the workshop region. |
| S3 | `aws s3api put-bucket-website --bucket "$FRONTEND_BUCKET" --website-configuration "{\"IndexDocument\":{\"Suffix\":\"index.html\"}}"` | Enables static website hosting on the frontend bucket. |
| S3 | `aws s3api get-bucket-website --bucket "$FRONTEND_BUCKET"` | Reads the current static website hosting configuration. |
| S3 | `aws s3api put-public-access-block --bucket "$FRONTEND_BUCKET" --public-access-block-configuration "{\"BlockPublicAcls\":false,\"IgnorePublicAcls\":false,\"BlockPublicPolicy\":false,\"RestrictPublicBuckets\":false}"` | Turns **Block Public Access OFF** for the frontend bucket (website bucket only). |
| S3 | `aws s3api put-bucket-policy --bucket "$FRONTEND_BUCKET" --policy "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"PublicReadForWebsiteFiles\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":[\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::$FRONTEND_BUCKET/*\"}]}"` | Attaches a bucket policy allowing public `s3:GetObject` for website files. |
| S3 | `aws s3 sync frontend/ "s3://$FRONTEND_BUCKET/" --region "$AWS_REGION"` | Uploads the local `frontend/` directory to the frontend bucket root. |
| S3 | `aws s3api put-public-access-block --bucket "$IMAGES_BUCKET" --public-access-block-configuration "{\"BlockPublicAcls\":true,\"IgnorePublicAcls\":true,\"BlockPublicPolicy\":true,\"RestrictPublicBuckets\":true}"` | Ensures **Block Public Access ON** for the private images bucket. |
| S3 | `aws s3api put-bucket-encryption --bucket "$IMAGES_BUCKET" --server-side-encryption-configuration "{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"AES256\"}}]}"` | Enables default encryption **SSE-S3** (AES-256) for the images bucket. |
| S3 | `aws s3api put-bucket-ownership-controls --bucket "$IMAGES_BUCKET" --ownership-controls "{\"Rules\":[{\"ObjectOwnership\":\"BucketOwnerEnforced\"}]}"` | Sets **Bucket owner enforced** (disables ACL-based ownership/permission confusion). |
| S3 | `aws s3api put-bucket-cors --bucket "$IMAGES_BUCKET" --cors-configuration "{\"CORSRules\":[{\"AllowedOrigins\":[\"http://localhost:8080\",\"REPLACE_WITH_WEBSITE_ORIGIN\"],\"AllowedMethods\":[\"PUT\",\"GET\",\"HEAD\"],\"AllowedHeaders\":[\"*\"],\"ExposeHeaders\":[\"ETag\"],\"MaxAgeSeconds\":3000}]}"` | Configures CORS on the images bucket for browser `PUT`/`GET` via presigned URLs. |
| HTTP | `curl -I "http://$FRONTEND_BUCKET.s3-website-ap-southeast-1.amazonaws.com/"` | Hits the **S3 website endpoint** root (should behave like a website; HTTP only). |
| HTTP | `curl -I "https://$FRONTEND_BUCKET.s3.ap-southeast-1.amazonaws.com/"` | Hits the **S3 REST endpoint** bucket root (often `403` because you did not grant listing). |
| HTTP | `curl -I "https://$FRONTEND_BUCKET.s3.ap-southeast-1.amazonaws.com/index.html"` | Hits the REST endpoint for a specific object (should work if public `GetObject` is allowed). |
| HTTP | `curl -I "https://$IMAGES_BUCKET.s3.ap-southeast-1.amazonaws.com/private-test.txt"` | Demonstrates private images bucket behavior (should be `AccessDenied`). |
| Lambda | `mkdir -p /tmp/cat-upload-lambda && rm -f /tmp/cat-upload-lambda/function.zip && cp backend/app.py /tmp/cat-upload-lambda/lambda_function.py && (cd /tmp/cat-upload-lambda && zip -r function.zip lambda_function.py)` | Packages Lambda code into a zip (using `lambda_function.handler`). |
| IAM | `aws iam create-role --role-name "cat-upload-api-role" --assume-role-policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}"` | Creates an IAM role that Lambda can assume. |
| IAM | `aws iam attach-role-policy --role-name "cat-upload-api-role" --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"` | Attaches CloudWatch Logs permissions (basic Lambda execution). |
| IAM | `aws iam put-role-policy --role-name "cat-upload-api-role" --policy-name "cat-upload-backend-runtime" --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:PutObject\",\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::$IMAGES_BUCKET/images/*\"},{\"Effect\":\"Allow\",\"Action\":[\"s3:ListBucket\"],\"Resource\":\"arn:aws:s3:::$IMAGES_BUCKET\",\"Condition\":{\"StringLike\":{\"s3:prefix\":[\"images/*\"]}}}]}"` | Grants Lambda permission to upload/list/get objects under `images/` in the private images bucket. |
| IAM | `export ROLE_ARN="$(aws iam get-role --role-name cat-upload-api-role --query 'Role.Arn' --output text)"` | Captures the role ARN for use when creating the Lambda function. |
| Lambda | `aws lambda create-function --function-name "$FUNCTION_NAME" --runtime "python3.12" --handler "lambda_function.handler" --role "$ROLE_ARN" --zip-file "fileb:///tmp/cat-upload-lambda/function.zip" --region "$AWS_REGION"` | Creates the Lambda function from the packaged zip. |
| Lambda | `aws lambda create-function-url-config --function-name "$FUNCTION_NAME" --auth-type NONE --cors "{\"AllowOrigins\":[\"*\"],\"AllowMethods\":[\"GET\",\"POST\",\"OPTIONS\"],\"AllowHeaders\":[\"content-type\"]}" --region "$AWS_REGION"` | Creates a public Function URL configuration with CORS. |
| Lambda | `aws lambda add-permission --function-name "$FUNCTION_NAME" --statement-id "FunctionUrlPublicInvoke" --action "lambda:InvokeFunctionUrl" --principal "*" --function-url-auth-type "NONE" --region "$AWS_REGION"` | Allows public invocation of the Function URL. |
| Lambda | `export FUNCTION_URL="$(aws lambda get-function-url-config --function-name "$FUNCTION_NAME" --query 'FunctionUrl' --output text --region "$AWS_REGION")"` | Retrieves the Function URL for testing / frontend config. |
| Lambda | `curl -sS -X POST -H "content-type: application/json" -d "{\"filename\":\"cat.jpg\",\"contentType\":\"image/jpeg\"}" "$FUNCTION_URL"` | Calls the backend to generate a presigned S3 PUT URL for uploads. |
| Lambda | `curl -sS "$FUNCTION_URL"` | Lists images (returns presigned GET URLs) from the backend. |
| Cleanup | `aws lambda delete-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION"` | Deletes the Lambda function. |
| Cleanup | `aws iam delete-role-policy --role-name "cat-upload-api-role" --policy-name "cat-upload-backend-runtime"` | Deletes the inline S3 runtime policy from the role (if you created it). |
| Cleanup | `aws iam detach-role-policy --role-name "cat-upload-api-role" --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"` | Detaches the AWS-managed logging policy from the role. |
| Cleanup | `aws iam delete-role --role-name "cat-upload-api-role"` | Deletes the IAM role (if you created it). |
| Cleanup | `aws s3 rm "s3://$IMAGES_BUCKET" --recursive --region "$AWS_REGION"` | Empties the images bucket. |
| Cleanup | `aws s3 rb "s3://$IMAGES_BUCKET" --force --region "$AWS_REGION"` | Deletes the images bucket. |
| Cleanup | `aws s3 rm "s3://$FRONTEND_BUCKET" --recursive --region "$AWS_REGION"` | Empties the frontend bucket. |
| Cleanup | `aws s3 rb "s3://$FRONTEND_BUCKET" --force --region "$AWS_REGION"` | Deletes the frontend bucket. |

