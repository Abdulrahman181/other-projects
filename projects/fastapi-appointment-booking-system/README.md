# FastAPI Appointment Booking System

A small appointment-booking application built with **FastAPI**, **SQLite**, **JWT authentication**, and static HTML pages.

## Components

- **Backend:** FastAPI + SQLite + JWT authentication (`main.py`)
- **Public website:** `index.html` for submitting appointments
- **Admin dashboard:** `admin.html` for viewing and managing appointments
- **Deployment configuration:** `render.yaml`
- **Environment template:** `.env.example`

## Project Structure

```text
fastapi-appointment-booking-system/
├── .env.example
├── README.md
├── admin.html
├── index.html
├── main.py
├── render.yaml
└── requirements.txt
```

## Configuration

Create the required environment variables before starting the backend:

```bash
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=YourStrongPassword123!
export SECRET_KEY=replace-with-a-long-random-secret
```

For production, use your hosting provider's secret-management settings rather than committing credentials to the repository.

## Run Locally

Install the dependencies:

```bash
pip install -r requirements.txt
```

Set the environment variables and start the application:

```bash
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=YourStrongPassword123!
export SECRET_KEY=replace-with-a-long-random-secret
uvicorn main:app --reload
```

The backend will be available at:

```text
http://localhost:8000
```

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

## Frontend Configuration

Before deploying the frontend, update the API URL in `index.html`:

```javascript
const API_URL = "https://YOUR-BACKEND-URL.onrender.com";
```

Update the API URL in `admin.html` as well:

```javascript
const API_URL = window.API_BASE_URL || "http://localhost:8000";
```

Use the deployed backend URL in both files when the application is hosted remotely.

## Deploy the Backend on Render

1. Create a Render account and connect GitHub.
2. Create a new Web Service from this repository.
3. Use the following build command:

   ```bash
   pip install -r requirements.txt
   ```

4. Use the following start command:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

5. Add these environment variables in the Render dashboard:

   | Variable | Description |
   |---|---|
   | `ADMIN_USERNAME` | The administrator username |
   | `ADMIN_PASSWORD` | A strong administrator password |
   | `SECRET_KEY` | A long random secret used for signing tokens |

6. Deploy the service and copy the public backend URL.
7. Replace the placeholder API URL in `index.html` and `admin.html` with the deployed backend URL.

## Deploy the Frontend

The static frontend can be served through GitHub Pages or another static hosting provider:

1. Configure `index.html` and `admin.html` with the deployed backend URL.
2. Enable GitHub Pages from **Settings → Pages** and select the `main` branch, or deploy the files to another static host.
3. Open the public page at the URL provided by the hosting provider.
4. Open `admin.html` to access the administration dashboard.

## Security Notes

- Never commit real passwords, JWT secrets, or production credentials.
- Use environment variables or a managed secret store for deployment credentials.
- Use a strong administrator password of at least 12 characters.
- The free Render plan may sleep after a period of inactivity; the first request after sleeping can take longer.
- JWT tokens expire according to the application configuration; users may need to sign in again after expiration.
- Consider using a password hash variable such as `ADMIN_PASSWORD_HASH` instead of storing a plain password when extending the application.

## Scope

This project is kept under the `other-projects` category because it is a standalone web application rather than an AI/ML model project.
