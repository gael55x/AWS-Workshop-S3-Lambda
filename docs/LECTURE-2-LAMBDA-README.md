# Lecture 2: AWS Lambda — Cat Upload backend

In Lecture 1, you built the boundary:

- a **public** S3 bucket that serves your website

- a **private** S3 bucket that will store uploads

Now you need the missing piece:

Your browser has to upload files to a private bucket…

…but you absolutely don’t want to hand out AWS credentials.

So today we introduce a tiny backend whose entire job is to sign *one* kind of permission: presigned URLs.

This lecture starts after Lecture 1 (`docs/LECTURE-1-S3-README.md`).

Before you start, keep `docs/INTRODUCTION.md` open in another tab — region constraint, repo map, prerequisites, and your fill-in notes live there.

## What we’re building

We deploy a single Lambda function exposed via a Function URL.

It does two things (same function, different HTTP method):

- **`POST`**: asks S3 for a presigned **PUT** URL so the browser can upload straight to the images bucket

- **`GET`**: returns a list of presigned S3 **GET** URLs so the gallery can display images while keeping the bucket private

Picture the boundary you built in Lecture 1:

- The frontend is **static** — S3 website hosting. Static sites can’t safely hold AWS credentials.
- The images bucket is **private**. That’s good, but it means direct browser uploads need a secure workaround.

That workaround is **presigned URLs**: short-lived, scoped permissions for exactly one operation.

Here’s the full request flow you’re about to build:

```text
1) Browser ──(POST)──> Lambda Function URL  ──(signs)──> presigned PUT URL
2) Browser ──(PUT)──>  S3 images bucket (private)
3) Browser ──(GET)──>  Lambda Function URL  ──(lists+signs)──> presigned GET URLs
```

One small naming note: you may see examples written like `POST /api/upload-url` to describe “the endpoint that returns an upload URL”.

In this workshop’s simplest deployment, we use a **Lambda Function URL with method-based routing** (no path routing):

- **POST** the **Function URL** → returns a presigned PUT URL
- **GET** the **Function URL** → returns presigned GET URLs for the gallery

So: treat “`/api/upload-url`” as a **conceptual label**, but implement it as **POST to the Function URL** in this repo.

## Lambda basics — just enough, right when we need it

Serverless compute means:

- You **run code without managing servers** (no instance provisioning, patching, capacity planning).
- You **pay for what you use** (compute time and requests, not idle servers).
- AWS provides and scales the **execution environment** (runtime, networking, isolation).

Quick positioning:

- **AWS Lambda**: best when you want an event-driven function and “true pay-as-you-go”.
- **AWS Fargate**: containers without server management; great when you want longer-running services or container-based workloads.
- **AWS App Runner**: easy request-driven web apps with built-in deployment flow; built on container infrastructure.

One misconception to fix early: it’s not “no servers” — it’s “**no servers you manage**”.

AWS Lambda runs your code when an event happens.

In our case, the “event” is an HTTP request coming in via a Function URL.

There are three words you’ll see in every Lambda example:

- **`handler`**: the Python function AWS executes

- **`event`**: a dictionary containing the request data (HTTP method, headers, the JSON body, etc.)

- **`context`**: info about the Lambda environment (we don’t really use it here, but it must be passed in)

### The anatomy of a function — handler, event, context

- **Handler**: your entrypoint. For this workshop it’s `handler(event, context)` and the Lambda Console handler string is `lambda_function.handler`.
- **Event**: “everything about the request.” With Function URLs, the HTTP method is nested under `requestContext.http.method` (you’ll see it if you print/log the event).
- **Context**: runtime metadata (timeouts, request id). We pass it because Lambda passes it, but we don’t need it for presigned URLs.

And one more term that matters for this workshop:

- A **Function URL** is an HTTPS endpoint attached directly to a Lambda function.

We use it instead of Amazon API Gateway to keep the workshop perfectly simple.

Lambda can be triggered by many things (S3 events, schedules, queues, streams, API Gateway, and more).

Today, we choose the simplest HTTP trigger that still feels “real-world”:

- **Lambda Function URLs**: a built-in HTTPS endpoint for your function.
- Perfect for a workshop and simple apps where you don’t need complex routing.

One clarification before we touch the Console:

Lambda does not automatically “have access to S3”.

Your Lambda function can only access S3 if you attach an **execution role** that allows it.

And for the love of all things good: **never** hardcode AWS access keys in code.

`boto3` automatically uses the execution role for you.

Here’s the permission chain we’re relying on:

```text
Lambda function  ──>  IAM execution role  ──>  S3 images bucket
```

<br>
<br>

## Prerequisites — Lambda session

- Permission to create Lambda functions and Function URLs.

- Permission to create/attach IAM roles and policies (or at least `iam:PassRole`).

- Your exact **images bucket** name from Lecture 1.

Notes (fill in):

- Images bucket: `____________________________________________`

- Function URL: `____________________________________________`

<br>
<br>

## Optional: Hello World Lambda

If you want a quick confidence check before the real build:

- Create a Lambda function with Python 3.12.
- Paste a minimal handler that returns `{ "message": "hello" }`.
- Click **Test** in-console once to see a successful JSON response.
- Then delete it (or just proceed) — the rest of this lecture is the real workshop function.

<br>
<br>

## Deployment checklist

Before the hands-on steps, say this out loud:

- Put your **images bucket name** into the Python code.
- Create the Lambda function (**Python 3.12**).
- Copy/paste the code into the browser editor and **Deploy**.
- Enable the **Function URL** (and CORS).

Then we do the detailed steps below.

> [!NOTE]
> Hands-on time: ask everyone to open the AWS Console and follow along step-by-step. Encourage them to pause you if they fall behind.

<br>
<br>

## Step 1: Prepare the code

The backend code needs to know where to upload files.

Open `backend/app.py` in your editor.

Find the `bucket = "..."` variable (around line 23) and replace the placeholder string with your real **images bucket** name.

> [!NOTE]
> We’re not shipping secrets—just telling the function which bucket it’s allowed to work with.

<br>
<br>

## Step 2: Create the Lambda function — Console

Now we’ll create one function to handle both uploading and listing.

For this workshop we intentionally keep it **one Lambda + one Function URL** and route based on HTTP method:

- **POST**: return a presigned PUT URL
- **GET**: return presigned GET URLs

From the Lambda Console → **Create function** → **Author from scratch**:

- **Function name**: `cat-upload-api`

- **Runtime**: Python 3.12

- **Architecture**: x86_64

- **Permissions**: “Create a new role with basic Lambda permissions”

Click **Create function**.

Under the **Code** tab, you will see an online text editor with `lambda_function.py`.

- **Copy** the entire contents of your local `backend/app.py` file.

- **Paste** it into the `lambda_function.py` file in the browser, replacing anything that was there.

Click the **Deploy** button (it will turn grey once deployed).

Now scroll down to **Runtime settings** and make sure the **Handler** says:

- `lambda_function.handler`

> [!NOTE]
> If you see `Runtime.HandlerNotFound` in CloudWatch logs, it almost always means the handler string is wrong.  
> In the current Lambda Console UI, “Runtime settings” may appear under the **Code** tab below the editor.  
> If you can’t find it, use your browser’s Find on the page for the word **Handler**.

Next, give the function permission to talk to your images bucket.

Under the **Configuration** tab → **Permissions** → click the Execution role name to open IAM.

In IAM:

- Click **Add permissions** → **Attach policies**

- Attach the policy defined by `iam/lambda/cat-upload-backend-runtime-policy.json`

Remember to replace the bucket name inside that JSON first.

> [!NOTE]
> IAM is the *only* reason Lambda can talk to S3. The policy is least-privilege: list only `images/`, and put/get only `images/*`.

<br>
<br>

## Step 3: Create a Function URL — Console

Your frontend needs an HTTP endpoint.

> [!NOTE]
> Function URLs are the simplest way to expose Lambda over HTTPS for this workshop.

Under the **Configuration** tab → **Function URL** → **Create function URL**:

- **Auth type**: NONE

- Expand **Configure CORS**:
  - **Allowed origins**: Put `*` to allow all origins for this workshop.
  - **Allowed methods**: Enable `GET, POST, OPTIONS`.
  - **Allowed headers**: `content-type`

> [!NOTE]
> If your function code already returns CORS headers (and handles `OPTIONS`), enabling Function URL CORS in the Console can cause the browser to reject responses with:  
> “`Access-Control-Allow-Origin` contains multiple values”.  
> If you hit that error, **disable Function URL CORS** and rely on the headers returned by the function code.

You now have an HTTPS Function URL.

Save it to your notepad.

<br>
<br>

## Step 4: Wire the frontend config

The frontend needs to know where the backend lives.

Edit `frontend/config.js` and set the single `apiBaseUrl`:

> [!NOTE]
> This frontend reads `window.CAT_UPLOAD_CONFIG.apiBaseUrl` at runtime.  
> The app trims trailing slashes, so either `...on.aws` or `...on.aws/` is fine.

```javascript
window.CAT_UPLOAD_CONFIG = {
  apiBaseUrl: "https://<your-id>.lambda-url.ap-southeast-1.on.aws/"
};
```

> [!NOTE]
> If you’re hosting the frontend from S3 website hosting, updating `frontend/config.js` locally is not enough.  
> You must **re-upload/sync** `config.js` to the frontend bucket, then hard refresh the page.  
> Smell-test: if the browser’s failed `POST` request URL is your **S3 website URL**, your bucket’s `config.js` is still old.

<br>
<br>

## Step 5: Test end-to-end

Open your frontend (either `http://localhost:8080` or your S3 static website URL).

Select a cat image and click Upload.

Now open DevTools → Network and watch what happens.

When it works, you can literally point at these requests:

1. **POST** to Function URL → backend returns a presigned upload URL (no AWS keys in the browser).
2. **PUT** directly to S3 → the file bytes go straight to your private bucket.
3. **GET** to Function URL → backend returns presigned view URLs so the gallery can render images.

You should see:

- `POST` to the Function URL (returns a presigned S3 upload URL)

- `PUT` straight to S3 to securely upload the object

Then the Gallery calls the same Function URL with `GET` and displays images using secure presigned GET URLs.

<br>
<br>

## Troubleshooting — Lambda session

- `Internal Server Error` (from backend):
  - Check CloudWatch Logs (Lambda → Monitor → View CloudWatch Logs). Look for Python tracebacks.
  - Ensure the Handler is set to `lambda_function.handler` and that you pasted the full `app.py` code into `lambda_function.py`.

- `AccessDenied` (from S3):
  - Confirm the Lambda execution role actually has the policy attached (scoped exactly to your bucket and `images/*`).

- CORS errors in the browser:
  - Confirm the images bucket CORS contains your exact frontend origin (from Lecture 1).
  - Confirm your Function URL CORS allows your frontend origin.
  - If you see “`Access-Control-Allow-Origin` contains multiple values”, you likely enabled Function URL CORS **and** your code is also returning `Access-Control-Allow-Origin`.
  - S3 CORS is strict: the origin must match **exactly** (`scheme://host`) with **no trailing slash**.

- Upload fails on the S3 `PUT` preflight (`OPTIONS` to S3) with “No `Access-Control-Allow-Origin` header”:
  - This is almost always the images bucket CORS origin mismatch (often an accidental trailing `/`), or a redirect due to a non-regional S3 endpoint.
  - Check the presigned upload URL hostname:
    - Prefer `https://<bucket>.s3.ap-southeast-1.amazonaws.com/...` over `https://<bucket>.s3.amazonaws.com/...`.
  - If needed, generate presigned URLs using a regional S3 client and SigV4 in `backend/app.py`:

```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    region_name="ap-southeast-1",
    endpoint_url="https://s3.ap-southeast-1.amazonaws.com",
    config=Config(signature_version="s3v4"),
)
```

- SignatureDoesNotMatch:
  - Ensure the frontend PUT `Content-Type` matches exactly what the backend presigned in Python.

<br>
<br>

## Cleanup — after Lecture 2

Console:

- Go to Lambda and delete the function (`cat-upload-api`).

- Optional: delete the execution role created for it (IAM → Roles).

S3 cleanup (do this to stop all charges):

- Go to S3 → Buckets:
  - Click into the **images bucket**, select all objects, and click **Delete**.
  - Empty the **frontend bucket**.
  - Go back to Buckets and delete both buckets entirely.
