# 🤖 AITradeAgent

AITradeAgent is an AI-powered trading agent platform that provides intelligent trading strategies, real-time market analysis, and portfolio management capabilities.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Docker Setup](#docker-setup)
- [API Documentation](#api-documentation)
- [Development](#development)

## ✨ Features

- 📊 Real-time market data analysis
- 🤖 AI-powered trading strategies
- 💼 Portfolio management
- ⚠️ Risk assessment and monitoring
- 📈 Interactive charts and visualizations
- 🔌 WebSocket support for live updates

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **Python 3.11+** - Programming language
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation using Python type hints
- **Uvicorn** - ASGI server
- **WebSockets** - Real-time communication

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **Recharts** - Charting library
- **WebSocket Client** - Real-time data streaming

## 📁 Project Structure

```
AITradeAgent/
├── backend/                    # Backend application
│   ├── app/
│   │   ├── api/               # API routes and endpoints
│   │   │   ├── __init__.py
│   │   │   └── routes.py      # Main API routes
│   │   ├── core/              # Core configuration
│   │   │   ├── __init__.py
│   │   │   └── config.py      # Settings and configuration
│   │   ├── models/            # Database models
│   │   │   └── __init__.py
│   │   ├── services/          # Business logic
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── main.py            # FastAPI application entry point
│   ├── tests/                 # Backend tests
│   │   ├── __init__.py
│   │   └── test_api.py
│   ├── Dockerfile
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Frontend application
│   ├── public/               # Static assets
│   ├── src/
│   │   ├── components/       # React components
│   │   │   └── Welcome.jsx
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   │   └── api.js
│   │   ├── utils/           # Utility functions
│   │   ├── App.jsx          # Main App component
│   │   ├── App.css
│   │   ├── main.jsx         # Entry point
│   │   └── index.css
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
├── .env.example             # Environment variables template
├── .gitignore
├── docker-compose.yml       # Docker Compose configuration
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn
- Docker and Docker Compose (optional)

### Local Development

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`:
```bash
cp ../.env.example .env
```

5. Run the backend server:
```bash
# From the backend directory
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at:
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

#### Database & Migrations

The backend uses SQLAlchemy for ORM mapping and Alembic for schema migrations. After configuring your `DATABASE_URL` in `.env`, apply the latest migrations:

```bash
cd backend
alembic upgrade head
```

When you update the models, generate a new migration and apply it:

```bash
cd backend
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

Alembic is configured to work with PostgreSQL in production and SQLite during local development, using batch mode for SQLite compatibility.

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file (optional):
```bash
echo "VITE_API_URL=http://localhost:8000" > .env
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5173

### Docker Setup

You can run the entire application using Docker Compose:

1. Make sure Docker and Docker Compose are installed

2. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

3. Build and run the containers:
```bash
docker-compose up --build
```

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

To stop the containers:
```bash
docker-compose down
```

## 📚 API Documentation

Once the backend is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints

- `GET /` - Root endpoint with API information
- `GET /api/v1/health` - Health check endpoint
- `GET /api/v1/` - API v1 root

## 💻 Development

### Running Tests

#### Backend Tests
```bash
cd backend
pytest
```

#### Frontend Tests
```bash
cd frontend
npm test
```

### Code Style

The project follows standard Python (PEP 8) and JavaScript/React conventions.

### Adding New Features

1. **Backend**: Add new routes in `backend/app/api/`, business logic in `backend/app/services/`, and models in `backend/app/models/`
2. **Frontend**: Add new components in `frontend/src/components/` and pages in `frontend/src/pages/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 📧 Contact

For questions and support, please open an issue in the repository.
