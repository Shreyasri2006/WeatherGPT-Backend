# Push this repository to GitHub

```bash
git init
git add .
git commit -m "Initial WeatherGPT SIH26068 backend"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/weathergpt-backend.git
git push -u origin main
```

Before deployment:
1. Copy `.env.example` to `.env` locally.
2. Never commit `.env` or API keys.
3. Configure `CORS_ORIGINS` with the deployed frontend URL.
4. Add the historical CSV locally/deployment storage if climate context is required.
