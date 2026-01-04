# Contributing to Self-Improving Prompt Optimization API

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## 🎯 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- **Clear title and description**
- **Steps to reproduce** the bug
- **Expected behavior** vs **actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Error messages** or logs (if applicable)

### Suggesting Features

We welcome feature suggestions! Please create an issue with:
- **Clear description** of the feature
- **Use case** or problem it solves
- **Proposed implementation** (if you have ideas)

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following our coding standards
4. **Test your changes** thoroughly
5. **Commit with clear messages**:
   ```bash
   git commit -m "Add: Description of your change"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request** with:
   - Clear title and description
   - Reference related issues
   - Screenshots (if UI changes)

## 📋 Coding Standards

### Python Code Style

- Follow **PEP 8** style guide
- Use **type hints** where appropriate
- Write **docstrings** for functions and classes
- Keep functions **focused and small**
- Use **meaningful variable names**

### Code Structure

- **API endpoints**: Add to `api/` directory
- **Core logic**: Add to appropriate service directories (`evaluation/`, `improvement/`, `storage/`)
- **Utilities**: Add to `utils/` directory
- **Tests**: Add to `tests/` directory (if created)

### Commit Messages

Use clear, descriptive commit messages:
- `Add: New feature description`
- `Fix: Bug description`
- `Update: What was updated`
- `Refactor: What was refactored`
- `Docs: Documentation changes`

## 🧪 Testing

Before submitting a PR:

1. **Test locally**:
   ```bash
   python3 main.py
   ```

2. **Test API endpoints**:
   - Visit http://localhost:8000/docs
   - Test your changes interactively

3. **Test frontend** (if UI changes):
   ```bash
   cd frontend
   python3 -m http.server 3000
   ```

## 🔍 Review Process

1. **Automated checks** will run on your PR
2. **Code review** by maintainers
3. **Feedback and iterations** (if needed)
4. **Approval and merge**

## 📝 Areas for Contribution

### High Priority

- **Tests**: Unit tests, integration tests
- **Documentation**: API docs, tutorials, examples
- **Error handling**: Better error messages and handling
- **Performance**: Optimization and caching improvements

### Feature Ideas

- **Additional LLM providers**: Support for more models
- **Evaluation metrics**: New evaluation dimensions
- **UI improvements**: Frontend enhancements
- **Deployment guides**: Docker, cloud deployment
- **Monitoring**: Logging and metrics

## 🚀 Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Hamzakhan7473/-Self-Improving-Prompt-Optimization-API.git
   cd "Self-Improving Prompt Optimization API"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the project**:
   ```bash
   python3 main.py
   ```

## 📚 Resources

- **Architecture**: See `README.md` for system architecture
- **API Documentation**: http://localhost:8000/docs (when running)
- **Research References**: See `RESEARCH_REFERENCES.md` (if available)

## ❓ Questions?

- **Open an issue** for questions or discussions
- **Check existing issues** for similar questions
- **Review the README** for setup and usage

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉

