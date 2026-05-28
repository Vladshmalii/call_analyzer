# Auto-Service AI Call Quality Control System

A high-performance, fault-tolerant, fully dockerized AI-powered call quality control system designed for auto services. This system automates compliance auditing for manager-client conversations by scanning Google Drive, performing local high-speed speech transcription, conducting deep LLM evaluation via Groq API, and saving structured, colorized reports directly to Google Sheets.

---

## Architecture Overview

This project is built using **Clean Architecture** patterns, separating business logic from adapters and external integrations:

- **Clean Architecture Domain separation**: API endpoints are strictly decoupled from DB models, repositories, and queue task executors.
- **Asynchronous Flow**: Uses Celery running separate isolated queues for speech transcription (CPU heavy) and API integrations (I/O heavy).
- **Beautiful Auditing**: Employs `structlog` to bind trace IDs across asynchronous processes, outputting structured logs and color-coded consoles.

---

## Project Structure

```
d:\test_analyze_call/
├── app/
│   ├── api/             # FastAPI routers, dependencies, and v1 aggregation
│   ├── ai/              # AI providers, schemas, prompts, and compliance analyzers
│   ├── core/            # Configuration settings, logging, database connections, exceptions
│   ├── integrations/    # External SDK adapters (Google Drive, Google Sheets, Groq API)
│   ├── models/          # SQLAlchemy 2.0 database models
│   ├── repositories/    # Clean DB CRUD interfaces
│   ├── schemas/         # Pydantic v2 schemas for request validation & API responses
│   ├── services/        # Central orchestrators (Google Drive, Google Sheets, CallProcessor)
│   ├── workers/         # Celery broker configuration and tasks
│   └── main.py          # FastAPI application entrypoint
├── tests/               # Pytest unit and integration tests
├── scripts/             # Database initialization scripts
├── docker-compose.yml   # Multi-service microservice layout
├── Dockerfile.api       # FastAPI container builder
├── Dockerfile.worker    # Celery worker container builder
├── requirements.txt     # Python production-grade packages
├── .env.example         # System configuration blueprint
└── README.md            # System operational guide
```

---

## Setup & Installations

### 1. Configure Environment Variables
Copy the configuration template:
```bash
cp .env.example .env
```
Fill in the configuration parameters inside `.env`:
- `GROQ_API_KEY`: Get a free key from the Groq Console.
- `GOOGLE_DRIVE_FOLDER_ID`: The ID of the Drive directory to scan for audio files.
- `GOOGLE_SHEET_ID`: The ID of the Google Sheet to update with results.

### 2. Configure Google Service Account Credentials
- Open Google Cloud Console, enable **Google Drive API** and **Google Sheets API**.
- Create a Service Account, generate a JSON Private Key, and save it in the root folder as `credentials.json`.
- Share your Google Drive Folder and Google Sheet with your service account email (e.g. `service-account@project.iam.gserviceaccount.com`) giving them **Editor** permissions.

---

## Running the System

Start the entire microservice ecosystem with a single command:
```bash
docker compose up --build
```

This starts:
1. **`postgres`**: Database storing calls, transcripts, analysis metrics, and job states.
2. **`redis`**: High-performance broker for Celery queues.
3. **`api`**: FastAPI server running on port `8000`.
4. **`worker-transcription`**: Isolated CPU Celery worker loading speech-to-text model on tiny footprint.
5. **`worker-general`**: General-purpose worker handling API uploads and Groq metrics.

### Verification Routes
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check status**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Realtime metrics**: [http://localhost:8000/api/v1/metrics](http://localhost:8000/api/v1/metrics)

---

## API Endpoints

- `GET /api/v1/health`: Audits Postgres and Redis connectivity.
- `GET /api/v1/metrics`: Provides aggregated compliance statistics (mean rating, violations counts).
- `GET /api/v1/calls`: Lists all ingested and analyzed phone logs.
- `GET /api/v1/calls/{id}`: Detailed analytical breakdown of a single call showing transcription segments, AI evaluations, and job histories.
- `POST /api/v1/reprocess/{id}`: Forces selective reprocessing of a failed processing pipeline.

---

## Troubleshooting

### Mount errors during startup
If Docker Compose raises mount errors regarding `credentials.json`, ensure that `credentials.json` file exists in your host directory before running `docker compose up`. A mock file is generated in the codebase by default to prevent engine crashes.

### Low system RAM during transcription
By default, the `FasterWhisperProvider` uses the `tiny` model to maximize CPU processing speed on standard virtual machines. If you have GPU power or large memory margins, change `model_size="base"` or `"small"` inside `app/services/transcription.py`.
