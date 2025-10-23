# Contributing to AITradeAgent

Thank you for your interest in contributing to AITradeAgent! This document provides guidelines and instructions for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/AITradeAgent.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Development

```bash
cd frontend
npm install
```

## Code Style

### Python (Backend)
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for classes and functions
- Keep functions small and focused
- Use meaningful variable names

### JavaScript/React (Frontend)
- Use functional components with hooks
- Follow React best practices
- Use camelCase for variables and functions
- Use PascalCase for component names
- Keep components small and reusable

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Commit Messages

- Use clear and descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Keep the first line under 50 characters
- Add detailed description if necessary

Example:
```
Add WebSocket support for real-time data

- Implement WebSocket connection manager
- Add echo endpoint for testing
- Update frontend to handle WebSocket messages
```

## Pull Request Process

1. Update documentation if you're changing functionality
2. Add tests for new features
3. Ensure all tests pass
4. Update the README.md if needed
5. Submit a pull request with a clear description of changes

## Questions?

If you have questions, please open an issue in the repository.
