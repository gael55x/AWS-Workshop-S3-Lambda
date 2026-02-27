## Lecture 1: Amazon S3

Picture this: you’ve got a tiny website where you want to upload cat photos.

- The **website** itself should be public (anyone can load HTML/CSS/JS).

- The **uploads** should stay private (random people shouldn’t be able to browse your bucket).

Today, we’ll build exactly that boundary with S3—*and we’ll intentionally stop right before uploads work*, because uploads require one extra ingredient you’ll add in Lecture 2.

Before you start, open [docs/INTRODUCTION.md](docs/INTRODUCTION.md) in another tab and keep it nearby (region constraint, repo map, prerequisites, and your fill-in notes live there).

<br>

## 1. S3 in one sentence: bucket + object

Suppose you want to put a file somewhere on AWS.

Where does it go?

**Creating A Public Bucket:**

In S3, files don’t live on servers you log into. They live inside something called a *bucket*.

Let’s create one.

1. Go to AWS Console.

2. Open **S3**.

3. Click **Create bucket**.

4. Bucket name example: `my-cat-workshop-frontend-<initials>-<digits>`

5. Region: `ap-southeast-1`

6. Leave default settings for now.

7. Click **Create bucket**.

Pause for a second.

Notice two things:

- AWS forces you to pick a **region** for the bucket.

- The name has to be **globally unique** (not “unique in your account”).

That’s intentional.

Amazon S3 is **object storage**: you store **objects** (bytes + metadata) inside **buckets**.

Let’s give those terms names:

- **Bucket**: the container.

- **Object**: a blob of bytes + metadata, stored in exactly one bucket.

And you never “SSH into” S3. Everything happens over HTTP — through the Console, CLI, SDKs, or browsers.


<br>

## 2. The “folder” that isn’t really a folder

Now, in the S3 Console, you’re going to see something that looks suspiciously like folders.

Let’s poke it.

**Creating a folder:**

1. Open the frontend bucket.

2. In the Objects tab, click **Create folder** → name it `images` → create.

3. Open the `images/` folder.

4. Click **Upload**.

5. Upload any file (example: `test.txt`).

6. Click the uploaded object.

7. Observe the **Object key** value.

Now look closely at what S3 calls the object’s name. You should see something like:

- `images/test.txt`

That full string — `images/test.txt` — is the object’s **key**.

If you remember exactly one mental model, make it this:

- **bucket + key = object location**

So what about “folders”?

S3 doesn’t have real folders. The Console is showing you a UI convenience: a *shared beginning* of keys.

Let’s give that a name too: a **prefix** is just a key “starts with” string (like `images/`).

- **Key**: the object’s full name inside the bucket (example: `images/cat.jpg`).

- Renaming/moving is effectively **copy + delete**, because you’re changing the key.

> [!NOTE]
> Later you’ll sync the real `frontend/` files from this repo. This `test.txt` is only for learning what a “key” is.



<br>

## 3. Turn the bucket into a website (and learn what a “website endpoint” is)

You’re about to use S3 in two different modes:

- as a **static website host** (for browsers)

- as a **storage API** (for CLI/SDK/presigned URLs)

**Static Website Hosting:**

Let’s start with the website mode.

1. Open the frontend bucket.

2. Go to **Properties**.

3. Scroll to **Static website hosting**.

4. Click **Enable**.

5. Index document: `index.html`

6. Save.

Now comes the natural question.

If this is a website… what URL does a browser actually visit?

Here’s the key idea.

S3 has a special hostname for static website hosting.

- It can serve `index.html` automatically at `/`.
- It is **HTTP only** on the S3 website endpoint (no HTTPS there).

Also important.

“Static hosting” here means S3 only serves files — it does not run backend code.

Let’s give that hostname a name:

- **Website endpoint**: looks like `http://<bucket>.s3-website-<region>.amazonaws.com`

There *is* also a different S3 hostname that behaves like an API (used by the CLI, SDKs, and presigned URLs).

We’ll name that one when we run into it on purpose in a minute.

> [!NOTE]
> Production reality check: if you want HTTPS + a CDN in front of S3 static hosting, put **CloudFront** in front of the bucket.



<br>

## 4. Making a website public (without making *everything* public)

A website is supposed to be readable by strangers. Your uploads are not.

So we’re going to do something that feels scary—“public”—but only for the website bucket, and only for **read**.

**Editing Bucket Permissions:**

Let’s do it carefully.

1. Open the frontend bucket.

2. Go to **Permissions**.

3. Under **Block public access**, turn OFF for this bucket only.
   - This bucket is intentionally public (it’s a website).
   - Never turn this off for your images bucket (the uploads bucket).

4. Go to **Bucket policy**.

5. Paste a public read policy for `arn:aws:s3:::YOUR_FRONTEND_BUCKET/*` (replace the bucket name):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadForWebsiteFiles",
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::YOUR_FRONTEND_BUCKET/*"
    }
  ]
}
```

Take 20 seconds and read that policy like a sentence:

“Allow **anyone** to **GET objects** from **this bucket**.”

Here’s how to decode it:

- `Principal: "*"` means “the public / anyone on the internet”.
- `Action: ["s3:GetObject"]` means “read objects” (not upload, not delete).
- `Resource: arn:aws:s3:::YOUR_FRONTEND_BUCKET/*` means “every object inside the bucket”.
  - The `/*` is important: it targets objects, not the bucket itself.

Notice what’s *not* here:

- `s3:ListBucket` is not granted, so the REST endpoint at the bucket root often returns `AccessDenied` (expected).

Now—don’t skim this. Look at the one action we’re actually allowing:

- `s3:GetObject`

That’s the point.

You did **not** make the bucket “admin-public.”

You made the objects in that bucket readable, which is exactly what a static website needs.

This is a **bucket policy** (resource-based permissions).

Helper: this policy is also available at `iam/s3/frontend-bucket-public-read-policy.json`.

> [!NOTE]
> Pitfall to catch now: forgetting to replace `YOUR_FRONTEND_BUCKET` in the policy is the fastest way to get confused later.




<br>

## 5. Put the website files in the bucket

Static website hosting doesn’t invent files—you have to upload them.

Let’s get the site in there.

If you have the AWS CLI configured, this is the fastest path:

```bash
aws s3 sync frontend/ s3://YOUR_FRONTEND_BUCKET/ --region ap-southeast-1
```

If you’re doing this purely in the Console, upload these files from this repo into the frontend bucket root:

- `frontend/index.html`

- `frontend/app.js`

- `frontend/styles.css`

- `frontend/config.js`

Now open the website endpoint in your browser (S3 → bucket → Properties → Static website hosting).

If you’re wondering why we’re using the weird `s3-website-...` URL instead of `s3.<region>.amazonaws.com`, this is why:

The website endpoint is the one that behaves like a website (root path → `index.html`).

Your URL will look like:

- `http://<frontend-bucket>.s3-website-ap-southeast-1.amazonaws.com`




<br>

## 6. The two-bucket pattern: public site, private uploads

If you put uploads in the same bucket as your website, you’ll eventually be tempted to “just make it public to fix it.”

We’re not doing that. We’re separating the boundary.

**Creating a Private Bucket:**

So now we create a second bucket: one for uploads.

1. Go back to S3 → Buckets → **Create bucket**.

2. Bucket name example: `my-cat-workshop-images-<initials>-<digits>`
   - In Lecture 2, you will paste this into the backend (`backend/app.py`) where it says `bucket = "..."`.

3. Region: `ap-southeast-1`

4. Leave defaults.

5. Click **Create bucket**.

Notice the default posture for a new bucket: it’s not publicly readable. That’s exactly what we want for uploads.

This is the **two-bucket pattern**:

- **Frontend bucket**: public read (static website)

- **Images bucket**: private by default (uploads)

The security win is not subtle: you can make the website bucket public without ever touching the images bucket’s public access settings.




<br>

## 7. Make “private” hard to mess up: Block Public Access, ownership, encryption

The biggest workshop accident is “I accidentally exposed the uploads bucket.”

So we add safety rails.

In the images bucket, we’re going to flip three switches that reduce confusion later.

First, **Block Public Access**:

- Go to **Permissions**

- Ensure **Block all public access = ON**

Next, **default encryption**:

- Go to **Properties**

- Confirm **SSE-S3** is enabled (it may already be ON by default).

Then, **object ownership**:

- Go to **Permissions**

- Set **Object Ownership** to **Bucket owner enforced**

**Proving A Bucket Is Private:**

Now let’s prove to ourselves the bucket is private.

1. Upload a file to the images bucket (example: `private-test.txt`).

2. Try to open it in a browser using:

```text
https://YOUR_IMAGES_BUCKET.s3.ap-southeast-1.amazonaws.com/private-test.txt
```

You should see:

- `AccessDenied`

Good.

That URL is the **REST endpoint** format.

Since the bucket is private and you didn’t provide credentials (or a presigned URL), S3 refuses.

Now we can name what you just used.

The **REST endpoint** is the API-style S3 endpoint used by:

- the **AWS CLI**

- **SDKs**

- **presigned URLs**

It supports **HTTPS**, and you interact with objects via operations like `GetObject` / `PutObject`.

It looks like:

- `https://<bucket>.s3.<region>.amazonaws.com/<key>`

And the debugging shortcut is simple:

- `s3-website-...` is the **website endpoint**

- `s3.<region>.amazonaws.com/...` is the **REST endpoint**

Let’s name the three “safety rails” you just set:

- **Block Public Access**: prevents accidental public policies/ACLs.

- **SSE-S3**: encrypts objects at rest by default (no app changes needed).

- **Bucket owner enforced**: disables ACL-based ownership (reduces permission confusion).

> [!NOTE]
> If you ever “fix” this by turning off Block Public Access on the images bucket, you’ve broken the design. Stop and undo it.




<br>

## 8. Two kinds of permissions: who you are vs what the bucket allows

You’ve already touched permissions in two ways:

- you made the **frontend bucket** publicly readable with a *bucket policy*

- you kept the **images bucket** private with bucket settings (and no public policy)

Now let’s connect that to the two permission systems you’ll hear about all the time in AWS.

Go compare your two buckets.

1. Open frontend bucket → **Permissions** → **Bucket policy** and review it.

2. Open images bucket → **Permissions** and confirm there is no public-read bucket policy.

Here’s the question that clears up a lot of confusion:

If *you* can upload files, but the public can’t read them… where is that difference expressed?

Two places, two perspectives:

- **IAM policies** attach to identities (users/roles) and answer: “Is *this identity* allowed to call S3?”

- **Bucket policies** attach to buckets and answer: “Is *this bucket* allowing or denying access to specific principals/actions/resources?”

Both apply at the same time.

So a useful way to think about it is:

- IAM answers: “Am I allowed to *try* this call?”
- Bucket policy answers: “Even if I can try… does the bucket allow *me* (or the public) to succeed?”

Anchor it to your workshop:

- Frontend bucket: bucket policy explicitly allows **public read** (`s3:GetObject`).

- Images bucket: no public bucket policy (private by default).


<br>

## 9. Same S3, different callers: browser vs CLI vs Lambda

Now let’s talk about *who* is making requests to S3, because debugging depends on this.

In this workshop you’ll see three access patterns:

- **Browser → S3**: loads the static website; later uses presigned PUT/GET (Lecture 2)

- **CLI → S3**: admin/operator actions from your terminal using AWS credentials

- **Lambda (SDK) → S3**: Lambda uses its execution role to talk to S3 (sign URLs, list objects)

Here’s the important part: you can learn the difference between “website hosting” and “S3 as an API” *without* having any AWS credentials at all.

If you haven’t logged in anywhere yet, that’s fine.

Once you have your bucket names and website URL written down (see `docs/INTRODUCTION.md`), you can run these from your terminal — no AWS CLI login required.

First, hit the website endpoint root (replace with your real website URL from Lecture 1):

```bash
curl -I "http://<frontend-bucket>.s3-website-ap-southeast-1.amazonaws.com/"
```

Now try the REST endpoint at the *bucket root*:

```bash
curl -I "https://YOUR_FRONTEND_BUCKET.s3.ap-southeast-1.amazonaws.com/"
```

You’ll usually get `403 AccessDenied` here.

That’s a good thing to notice: your bucket policy allowed `s3:GetObject` (read objects), but it did **not** make the bucket listable.

Now try the REST endpoint for a *specific object* you know exists:

```bash
curl -I "https://YOUR_FRONTEND_BUCKET.s3.ap-southeast-1.amazonaws.com/index.html"
```

That should return `200` (or at least not `AccessDenied`), because this is an object GET.

Finally, try the same idea against the private images bucket (use the `private-test.txt` object you uploaded earlier):

```bash
curl -I "https://YOUR_IMAGES_BUCKET.s3.ap-southeast-1.amazonaws.com/private-test.txt"
```

That should be `AccessDenied`, because the images bucket is private by design.

If you *are* authenticated with the AWS CLI, here’s the equivalent “operator view” (optional):

```bash
aws s3 ls s3://YOUR_FRONTEND_BUCKET/ --region ap-southeast-1

aws s3 ls s3://YOUR_IMAGES_BUCKET/ --region ap-southeast-1
```

And in Lecture 2, Lambda will call S3 using the AWS SDK (`boto3`) with an execution role.

Keep this mental map in your head (we’ll use it again in Lecture 2):

```text
Lecture 1
Browser ──(GET)──> S3 Website Bucket (public)

Lecture 2
Browser ──(POST/GET)──> Lambda Function URLs (backend API)
Lambda  ──(SDK/IAM)──> S3 Images Bucket (private)
Browser ──(PUT/GET via presigned URL)──> S3 Images Bucket (private)
```


<br>

## 10. When it fails, what kind of failure is it?

Most confusion in this workshop comes from mixing up two very different kinds of failure:

1. The **browser** refuses to send/accept a cross-origin request (CORS).
2. **S3** receives the request and says “no” (`AccessDenied`, signature errors).

Here are two rules of thumb that will save you time:

- **CORS only affects the browser.**
- **IAM affects everything** (browser, CLI, Lambda).

So when you’re debugging:

- **CORS error in the browser console** = browser blocked the request

- **403 AccessDenied (or signature errors) from S3** = permissions/policy/signature issue (not a CORS “grant”)



<br>

## 11. CORS: the browser’s rule (not AWS permission)

Browsers don’t do cross-origin writes silently. They ask first.

In Lecture 2, your browser will `PUT` directly to the images bucket using a presigned URL. That’s cross-origin.

**Configuring CORS:**

So we configure CORS now, while we’re still in “S3 mode.”

1. Go to images bucket.
2. **Permissions** → **CORS configuration**.
3. Paste (replace origins):

```json
[
  {
    "AllowedOrigins": [
      "http://localhost:8080",
      "REPLACE_WITH_WEBSITE_ORIGIN"
    ],
    "AllowedMethods": ["PUT", "GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

Be careful with the replacement for `REPLACE_WITH_WEBSITE_ORIGIN`.

Use the **origin only** (scheme + host). For example:

- `http://yourname-cat-upload-frontend.s3-website-ap-southeast-1.amazonaws.com`

Not the full path. Not `.../index.html`. Just the origin.

Two more details that matter when you’re debugging:

- Most browsers send an `OPTIONS` **preflight** request before a cross-origin `PUT`.
- CORS does not affect the CLI or your backend.
- CORS does **not** grant AWS permissions.
  - It only tells the browser “this cross-origin request is allowed to be sent/accepted.”


<br>

## 12. Presigned URLs (why Lecture 2 exists)

Right now your images bucket is private on purpose.

So the browser is stuck:

- it needs to upload

- but it must not receive your AWS credentials

So how does the browser upload without AWS keys?

A **presigned URL** is the bridge: a short-lived signed permission for one specific request.

If you’ve never seen one before, here’s what it looks like.

It’s basically a normal S3 REST URL (bucket + key) plus a signed query string.

**Example (presigned PUT URL for upload, redacted):**

```text
https://<images-bucket>.s3.ap-southeast-1.amazonaws.com/images/7f2c9b2b8c5b4a1f9b2d3c4e5f6a7b8c.jpg
?X-Amz-Algorithm=AWS4-HMAC-SHA256
&X-Amz-Credential=<REDACTED>%2F20260226%2Fap-southeast-1%2Fs3%2Faws4_request
&X-Amz-Date=20260226T010203Z
&X-Amz-Expires=300
&X-Amz-SignedHeaders=content-type%3Bhost
&X-Amz-Security-Token=<MAY_APPEAR_FOR_TEMP_CREDS>
&X-Amz-Signature=<REDACTED>
```

**Example (presigned GET URL for download, redacted):**

```text
https://<images-bucket>.s3.ap-southeast-1.amazonaws.com/images/7f2c9b2b8c5b4a1f9b2d3c4e5f6a7b8c.jpg
?X-Amz-Algorithm=AWS4-HMAC-SHA256
&X-Amz-Credential=<REDACTED>%2F20260226%2Fap-southeast-1%2Fs3%2Faws4_request
&X-Amz-Date=20260226T010203Z
&X-Amz-Expires=300
&X-Amz-SignedHeaders=host
&X-Amz-Security-Token=<MAY_APPEAR_FOR_TEMP_CREDS>
&X-Amz-Signature=<REDACTED>
```

Now look at what’s doing the work.

- The host + path (`<bucket>.s3.<region>.amazonaws.com/images/...`) still points to **bucket + key**.
- `X-Amz-Expires=300` is the lifetime (5 minutes in this workshop).
- `X-Amz-SignedHeaders=...` tells you which headers are part of the signature.
  - This is why headers can matter: for **PUT**, `Content-Type` often has to match what was signed.
- `X-Amz-Signature=...` is the proof: someone with permission signed *this exact request shape*.
- `X-Amz-Security-Token` may appear when the signer is using temporary credentials (like Lambda’s execution role).

Presigned URLs are “permission for **one request shape**”:

- method matters (PUT vs GET)

- key matters (`images/...`)

- headers can matter (especially `Content-Type`)

And a presigned URL only works if the signer (your backend’s role) is allowed to do the underlying action:

- `s3:PutObject` for uploads

- `s3:GetObject` for downloads

- `s3:ListBucket` to list keys under the `images/` prefix

Lecture 2 adds Lambda so your backend can sign these URLs safely, while the images bucket stays private.


<br>

## 13. Stop point (end of Lecture 1)

Let’s zoom out and take inventory.

At this point, you should have:

- A working static website hosted from S3 (frontend bucket).

- A private images bucket with:
  - Block Public Access ON
  - Encryption enabled (SSE-S3)
  - Ownership enforced (bucket owner enforced)
  - CORS configured (so browser uploads can work in Lecture 2)

And one important non-feature:

- Uploading from the browser is **not** working yet. That’s intentional.

### Quick “don’t step on rakes” reminders

- Don’t turn off Block Public Access for the images bucket.
- Don’t put a full URL path in CORS origin (origin is only `scheme://host`).

### Production reality check (keep it in your peripheral vision)

- Put CloudFront in front of S3 for HTTPS + caching.
- Use a custom domain and HTTPS everywhere.
- Tighten IAM policies to the minimum bucket + prefix + actions needed.




## Cost notes

You pay for:

- storage (GB-month)
- requests (PUT, GET, LIST)
- data transfer out to the internet

## Cleanup (after Lecture 1)

No cleanup yet.

This workshop continues into Session 2. Do the full cleanup at the end of Lecture 2 (`docs/LAMBDA-README.md`).
