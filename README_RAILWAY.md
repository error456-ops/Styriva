# STYRIVA — Railway deployment starter (Django + PostgreSQL)

These files are tailored to the uploaded project files: Django 5.2.5, project package `STYRIVA`, PostgreSQL, Cloudinary, OpenAI and Razorpay.

## Files
- `requirements.txt` — initial dependency list inferred from your uploaded settings and README. It may need additions for imports used in your app files.
- `railway.json`, `railway_start.sh`, `Procfile` — Railway deploy/start configuration.
- `settings_railway.py` — production-oriented replacement candidate based on your uploaded settings. Review carefully before copying it to `STYRIVA/settings.py`.
- `.env.example` — variable names only; no real secrets.
- `.gitignore` — excludes `.env` and local files.

## Steps
1. Copy these files into the repository root, next to `manage.py`.
2. Review `settings_railway.py`. If you use it, replace `STYRIVA/settings.py` with its contents and commit the change. Keep a backup of your current settings.
3. In Railway, add a PostgreSQL service and set the web service's `DATABASE_URL` to a reference to the PostgreSQL service's connection URL.
4. Add Railway Variables: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `OPENAI_API_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.
5. Generate a Railway public domain, then set `ALLOWED_HOSTS` to the hostname only (no `https://`) and `CSRF_TRUSTED_ORIGINS` to the full HTTPS origin.
6. Push to GitHub and deploy. The start script runs migrations, collects static files, and starts Gunicorn.

## Security — do this before deployment
The settings file you uploaded contains a hard-coded Django `SECRET_KEY` and a hard-coded local database password. Do not reuse those values in production. Replace the Django secret with a new random value and keep it only in Railway Variables. If the database password is used anywhere outside a disposable local database, rotate it too. Do not upload `.env` to GitHub.

## Notes
- `requirements.txt` is an initial best-effort list based on the files available, not a verified lockfile. I have not seen all app source files or their imports, so deployment may reveal additional required packages.
- If OpenCV is imported in your code, `opencv-python-headless` is suitable for server environments in most cases.
- If your app uses a separate background worker/Celery task queue, that worker needs its own Railway service and start command; these uploaded files did not include enough worker code to configure it.
- If the project uses any custom PostgreSQL extensions or special database settings, review those before deploying.
