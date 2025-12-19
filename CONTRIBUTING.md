# Contributing to Federated RAG System

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Report issues professionally
- Help others learn and grow

## How to Contribute

### 1. Fork the Repository
```bash
# Go to https://github.com/Anis196/federated-rag-system
# Click "Fork" button
```

### 2. Clone Your Fork
```bash
git clone https://github.com/YOUR_USERNAME/federated-rag-system.git
cd federated-rag-system
```

### 3. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-name
```

**Branch naming convention:**
- Features: `feature/feature-name`
- Bug fixes: `fix/bug-name`
- Documentation: `docs/doc-name`

### 4. Make Your Changes

Follow the project structure:
- **Python Service:** `python-rag-service/`
- **Backend:** `backend/`
- **Frontend:** `frontend/`

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature" 
```

**Commit message format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Code style (formatting, missing semicolons)
- `refactor:` - Code restructuring
- `test:` - Adding/updating tests
- `chore:` - Build process, dependencies

**Example:**
```
feat: add RAG query caching
fix: resolve CORS issue with frontend
docs: update API reference
```

### 6. Push to Your Fork
```bash
git push origin feature/your-feature-name
```

### 7. Create a Pull Request

1. Go to https://github.com/Anis196/federated-rag-system
2. Click "Compare & pull request"
3. Fill in:
   - **Title:** Clear, descriptive title
   - **Description:** What changes? Why? How?
   - **Related issues:** Reference any related issues (e.g., Fixes #123)

---

## Development Setup

Before contributing, set up your local environment:

### Python Service
```bash
cd python-rag-service
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
python main.py
```

### Backend
```bash
cd backend
mvn clean package -DskipTests
java -jar target/springboot-rag-chat-0.0.1-SNAPSHOT.jar
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

See [SETUP_LOCAL.md](SETUP_LOCAL.md) for detailed instructions.

---

## Project Structure

```
federated-rag-system/
├── python-rag-service/     # FastAPI RAG service
│   ├── docs/               # Component documentation
│   ├── main.py             # Entry point
│   └── requirements.txt     # Python dependencies
├── backend/                # Spring Boot REST API
│   ├── docs/               # Component documentation
│   ├── pom.xml             # Maven configuration
│   └── src/                # Java source code
├── frontend/               # React UI
│   ├── docs/               # Component documentation
│   ├── package.json        # Node dependencies
│   └── src/                # React source code
├── README.md               # Project overview
├── SETUP_LOCAL.md          # Local setup guide
├── CONTRIBUTING.md         # This file
└── LICENSE                 # MIT License
```

---

## Testing

### Run Tests
```bash
# Python service
cd python-rag-service
pytest tests/

# Backend
cd backend
mvn test

# Frontend
cd frontend
npm test
```

### Manual Testing
1. Start all three services (see SETUP_LOCAL.md)
2. Open http://localhost:8080
3. Test various queries
4. Check browser console for errors
5. Check service logs for issues

---

## Code Style Guidelines

### Python
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where possible
- Maximum line length: 100 characters
- Use descriptive variable names

### Java
- Follow [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- Use meaningful variable names
- Add Javadoc comments for public methods
- Proper package structure

### TypeScript/React
- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use meaningful component names
- Prefer functional components with hooks
- Keep components small and focused
- Use TypeScript for type safety

---

## Documentation

When contributing, please update relevant documentation:

- Update [README.md](README.md) if adding features
- Update component docs in `docs/` folders
- Update [SETUP_LOCAL.md](SETUP_LOCAL.md) if changing setup process
- Add inline comments for complex logic
- Keep documentation up-to-date with code changes

---

## Reporting Issues

### Bug Reports
Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python/Java/Node version)
- Screenshots/logs if applicable

### Feature Requests
Include:
- Clear description of the feature
- Why it's needed
- Suggested implementation (if any)
- Use cases/examples

---

## Pull Request Process

1. **Ensure tests pass:**
   ```bash
   # Run tests before pushing
   pytest  # Python
   mvn test  # Java
   npm test  # Frontend
   ```

2. **Update documentation:**
   - Update README if needed
   - Update component docs
   - Add comments for complex code

3. **Keep commits clean:**
   - Rebase if needed
   - Avoid merge commits
   - Squash related commits

4. **PR Review:**
   - Address reviewer feedback
   - Make requested changes
   - Re-request review after updates

5. **Merge:**
   - Use "Squash and merge" for feature branches
   - Use "Create a merge commit" for hotfixes

---

## Areas for Contribution

### High Priority
- [ ] Add comprehensive unit tests
- [ ] Improve error handling
- [ ] Add API rate limiting
- [ ] Optimize embedding generation
- [ ] Add caching mechanisms

### Medium Priority
- [ ] Improve UI/UX
- [ ] Add more data format support
- [ ] Enhance documentation
- [ ] Add performance monitoring
- [ ] Improve logging

### Low Priority
- [ ] Add themes/styling options
- [ ] Refactor legacy code
- [ ] Add more examples
- [ ] Improve comments

---

## Questions?

- **Issues:** Use GitHub Issues for bug reports and feature requests
- **Discussions:** Use GitHub Discussions for questions
- **Documentation:** Check relevant docs in each component's `docs/` folder
- **Email:** Reach out to the maintainers

---

## License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for contributing! 🚀
