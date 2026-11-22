# Deployment
No Docker required. Any host that runs Python 3.11: `pip install -r requirements.txt && uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`. Set secrets via environment (see .env.example). Production: managed Postgres+PostGIS, set DATABASE_URL, put media in S3-compatible storage, front with HTTPS. CI: GitHub Actions runs pytest on push/PR.
