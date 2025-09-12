## Step 3 - API Endpoints

1. Add dependencies and rebuild:
```bash
docker compose build api
docker compose up -d
docker compose exec api poetry install
