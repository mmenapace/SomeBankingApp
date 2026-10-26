# Simple Banking Application

This project contains a FastAPI banking API and an Angular frontend. The frontend calls the API at `http://127.0.0.1:8000`.

## Requirements

- Python 3.10 or later
- Node.js and npm (for the frontend)

## Run the application

Start the backend and frontend in separate terminals.

### 1. Start the backend

From the `backend` directory, create and activate a virtual environment, then install the API dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install fastapi sqlalchemy uvicorn
```

If PowerShell prevents activation, use the virtual environment's interpreter directly for the install and launch commands:

```powershell
.\.venv\Scripts\python.exe -m pip install fastapi sqlalchemy uvicorn
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Otherwise, with the environment activated, launch the API:

```powershell
python -m uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive API documentation is at `http://127.0.0.1:8000/docs`.

The SQLite database is stored in `backend/bank.db`. If it does not exist, the application creates it on startup.

### 2. Start the frontend

In a second terminal, change to `frontend/SomeBankingFrontend` and install the dependencies:

```powershell
npm ci
npm start
```

Open `http://localhost:4200` in your browser. The backend allows requests from this local frontend origin.

## Notes

This application is a demonstration backend, not a production banking system. It uses a local SQLite database and includes a starter balance when creating a user.
