## Workshop introduction (read this once)

### One constraint for the whole workshop (don’t ignore this)

> [!NOTE]
> Use `ap-southeast-1` for everything in this workshop.

> [!IMPORTANT]
> Keep **all workshop resources in the same region** (`ap-southeast-1`): both S3 buckets (Lecture 1) and Lambda functions (Lecture 2).

### Repo map (just enough to navigate)

```text
.
├─ frontend/     # static website files
├─ backend/      # Lambda (Python) handlers for Function URLs
└─ iam/          # least-privilege policy templates (JSON)
```

### Where Lambda fits (Session 2)

In Session 2 (`docs/LAMBDA-README.md`), you’ll deploy two Lambda functions (via Function URLs):

- **Upload URL** (POST): returns a presigned S3 PUT URL
- **List images** (GET): returns presigned S3 GET URLs (so the images bucket can stay private)

### Prerequisites

- **Required**
  - AWS account access to use the S3 Console (create buckets, edit permissions)
  - Python 3 (for running a local static server)
- **Optional (only if you will use CLI commands)**
  - AWS CLI v2
  - AWS credentials configured in your shell (SSO/profile)

### Notes to fill in as you go (keep this section handy)

#### Session 1 (S3)

- Frontend bucket: `____________________________________________`
- Images bucket (used later in Lecture 2 backend code): `____________________________________________`
- Frontend website URL: `____________________________________________`
- Frontend website origin (for CORS): `____________________________________________`
- Local origin (for CORS): `http://localhost:8080`

#### Session 2 (Lambda)

- Upload URL function URL: `____________________________________________`
- List images function URL: `____________________________________________`
