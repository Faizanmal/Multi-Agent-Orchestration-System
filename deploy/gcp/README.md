# GCP Cloud Run deploy (recommended)

**Stack**

| Layer | Service |
|-------|---------|
| Frontend | Vercel |
| API | Cloud Run (`multi-agent-api`) |
| Celery worker | Cloud Run (`multi-agent-worker`) |
| Postgres | Neon or Supabase |
| Redis | Upstash (`rediss://`) |

No Cloud SQL, Memorystore, or VPC connector required.

---

## 1. Create managed data stores

### Neon or Supabase
1. Create a project.
2. Copy the **pooled** Postgres URL (include `?sslmode=require`).
3. Example: `postgresql://user:pass@ep-….neon.tech/neondb?sslmode=require`

### Upstash
1. Create a Redis database.
2. Copy the **Redis URL** (`rediss://default:…@….upstash.io:6379`).
3. Use the **same URL** for `REDIS_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` (Upstash is DB `0` only).

### Vercel
1. Deploy `frontend/` (Root Directory = `frontend`).
2. Note the URL: `https://your-app.vercel.app` (set API env vars in step 4).

---

## 2. Configure secrets locally

```bash
cp deploy/gcp/.env.cloudrun.example deploy/gcp/.env.cloudrun
# Edit: GOOGLE_CLOUD_PROJECT, SECRET_KEY, DATABASE_URL, REDIS_URL,
#       FRONTEND_URL, CORS_*, GROQ_API_KEY, etc.
```

---

## 3. Deploy API + worker

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
# gcloud auth login   # if needed
bash deploy/gcp/deploy-cloudrun.sh
```

This will:
- Enable Cloud Run / Cloud Build / Artifact Registry / Secret Manager
- Push secrets from `.env.cloudrun`
- Build the backend image
- Deploy **API** (`SERVICE_ROLE=web`, min=0, max=1, public HTTPS)
- Deploy **worker** (`SERVICE_ROLE=worker`, min=0, max=1)

Defaults are lean (scale to zero). For fewer Celery delays, set worker `_WORKER_MIN_INSTANCES=1` in the submit substitutions.

---

## 4. Wire Vercel ↔ Cloud Run

After deploy, script prints `API_URL` like `https://multi-agent-api-xxxxx-uc.a.run.app`.

**Vercel → Project → Settings → Environment Variables**

| Name | Value |
|------|--------|
| `NEXT_PUBLIC_API_URL` | `https://multi-agent-api-xxxxx-uc.a.run.app` |
| `NEXT_PUBLIC_WS_URL` | `wss://multi-agent-api-xxxxx-uc.a.run.app` |

Redeploy the frontend.

**Backend `.env.cloudrun` (then re-run secrets + build once)**

```env
ALLOWED_HOSTS=multi-agent-api-xxxxx-uc.a.run.app,.run.app
FRONTEND_URL=https://your-app.vercel.app
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-app.vercel.app,https://multi-agent-api-xxxxx-uc.a.run.app
```

```bash
bash deploy/gcp/setup-secrets.sh
gcloud builds submit --config=deploy/gcp/cloudbuild.yaml
```

---

## 5. Verify

```bash
curl https://YOUR-SERVICE.run.app/health/live/
# Expect: {"alive": true, ...}
```

Open the Vercel app → login / chat.

---

## Sizing & cost (ballpark)

| Setting | Default in `cloudbuild.yaml` |
|---------|------------------------------|
| API min / max | 0 / 1 |
| Worker min / max | 0 / 1 |
| Memory / CPU | 2Gi / 2 |

Idle cost is mostly Neon/Supabase/Upstash free tiers + tiny Cloud Run usage.  
Set worker `min=1` if background jobs must not wait for a cold start (~+$25–55/mo).

---

## Useful commands

```bash
# Logs
gcloud run services logs read multi-agent-api --region=us-central1 --limit=50
gcloud run services logs read multi-agent-worker --region=us-central1 --limit=50

# Update only secrets
bash deploy/gcp/setup-secrets.sh

# Delete
gcloud run services delete multi-agent-api --region=us-central1 --quiet
gcloud run services delete multi-agent-worker --region=us-central1 --quiet
```

---

## Optional: Compute Engine VM

If you prefer one VM with Docker Compose (Postgres/Redis on-box), see the older scripts:
`create-instance.sh`, `vm-setup.sh`, `docker-compose.gce.yml`.
That path does **not** give free HTTPS without a domain.
