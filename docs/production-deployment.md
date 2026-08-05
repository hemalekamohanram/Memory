# Production deployment guide

This guide deploys the Engram API and consolidation worker to AWS `us-west-2`, alongside a CockroachDB Cloud cluster in the same region. It is designed for a hackathon demo and documents the production hardening boundary clearly.

## What is deployed

| Component | Service | Purpose |
| --- | --- | --- |
| API | Amazon API Gateway + AWS Lambda | Hosts the FastAPI/Mangum application. |
| Consolidation | AWS Lambda | Runs idempotent memory-consolidation work. |
| Evidence archive | Amazon S3 | Private, encrypted, versioned evidence artifacts. |
| Models | Amazon Bedrock | Nova 2 Lite for extraction/answers; Titan Text Embeddings V2 for vectors. |
| Memory system | CockroachDB Cloud | Transactional memories, provenance, audits, and vector index. |
| Web UI | AWS Amplify Hosting | Hosts the static Next.js UI from GitHub. |

## 1. CockroachDB Cloud

1. Create a Standard CockroachDB Cloud cluster in AWS `us-west-2`.
2. Create an application SQL user named `engram_app` and a database named `engram`.
3. Download the cluster CA certificate to the PostgreSQL certificate location recommended by the Cloud console.
4. Build a TLS URL, URL-encoding only special characters in the password:

```text
postgresql+psycopg://engram_app:<URL_ENCODED_PASSWORD>@<HOST>:26257/engram?sslmode=verify-full
```

5. Save that URL only in your untracked local `.env` and later enter it into the SAM `DatabaseUrlParameter` prompt. Never commit it.
6. Run the schema migration from a machine with the URL configured:

```powershell
alembic upgrade head
```

7. In the CockroachDB Cloud SQL shell, run the vector-index commands one at a time. The cluster setting cannot run inside Alembic's migration transaction:

```sql
SET CLUSTER SETTING feature.vector_index.enabled = true;
CREATE VECTOR INDEX IF NOT EXISTS memories_embedding_idx
ON memories (organization_id, project_id, embedding vector_cosine_ops);
SHOW INDEXES FROM memories;
```

8. Configure the CockroachDB Cloud Managed MCP endpoint using the console-generated OAuth connection. Select read-only consent. The MCP client should inspect schema, index state, and retrieval traces; it must not contain a SQL password.

## 2. Amazon Bedrock

1. In AWS `us-west-2`, open Amazon Bedrock Model catalog.
2. Select the serverless **Global Amazon Nova 2 Lite** inference profile. Do not purchase provisioned throughput.
3. Confirm a small playground request works.
4. Enable access to `amazon.titan-embed-text-v2:0` if Bedrock requests access before first use.

Engram defaults to `global.amazon.nova-2-lite-v1:0`. Bedrock is usage-priced; there is no idle model capacity charge for this serverless profile.

## 3. Deploy the API, worker, and evidence bucket

Use AWS CloudShell so you do not need to create local AWS access keys:

```bash
git clone https://github.com/hemalekamohanram/Memory.git
cd Memory
sam build --template-file infrastructure/aws/template.yaml
sam deploy --guided
```

Use stack name `engram-hackathon`, region `us-west-2`, and enter the CockroachDB URL only at the `DatabaseUrlParameter` prompt. Keep the default Bedrock model. Use `http://localhost:3000` as `WebOrigin` for the first deploy; it will be replaced after Amplify creates the public frontend URL.

The SAM template creates an encrypted versioned S3 bucket, API Gateway, the API Lambda, and a worker Lambda. It grants only the required S3 and Bedrock actions to those functions.

After deployment, copy the `ApiUrl` output and verify:

```bash
curl <ApiUrl>/health
curl <ApiUrl>/ready
```

## 4. Deploy the web app with Amplify

1. In AWS Amplify, choose **New app** then **Host web app**.
2. Connect GitHub repository `hemalekamohanram/Memory`, branch `main`.
3. Set the app root to `apps/web`.
4. Add the environment variable `NEXT_PUBLIC_API_URL` with the API Gateway `ApiUrl` output.
5. Use this build configuration:

```yaml
version: 1
applications:
  - appRoot: apps/web
    frontend:
      phases:
        preBuild:
          commands:
            - corepack enable
            - pnpm install --frozen-lockfile
        build:
          commands:
            - pnpm build
      artifacts:
        baseDirectory: .next
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*
```

6. Deploy. Copy the resulting `https://...amplifyapp.com` URL.
7. Redeploy the SAM stack with `WebOrigin` set to that exact Amplify URL. This limits browser CORS to the hosted UI.

## 5. End-to-end verification

Run these checks only after the public frontend and API are live:

1. Open the public app and create the demo project.
2. Seed the demo memories.
3. Create a fresh session and ask: `How should parallel refresh requests avoid intermittent logouts?`
4. Confirm the answer refers to serializable token rotation and retries.
5. Open Memory Trace and confirm candidate scores and selection reasons are visible.
6. Open Decision Graveyard and Agent Handoff.
7. In Managed MCP, inspect the vector index or read-only retrieval trace.
8. Check CloudWatch logs for API and worker errors; do not include credentials or raw sensitive evidence in logs.

## Operations and shutdown

Set an AWS Budget alert before deployment. Delete the CloudFormation stack after the demo if it is no longer needed; empty the generated S3 bucket if CloudFormation reports that it cannot delete a non-empty bucket. Stop or delete the CockroachDB cluster separately when judging is over. S3 storage, backups, and CockroachDB storage can continue to incur usage charges even after compute is stopped.

## Security boundary

The public hackathon deployment contains only seeded demo data. A production rollout must add identity-provider authentication in front of the API, use AWS Secrets Manager rather than a CloudFormation parameter for the database URL, restrict Bedrock IAM resources to approved model ARNs, apply S3 lifecycle/retention policies, configure CloudWatch alarms, and load-test tenant isolation and recovery procedures.
