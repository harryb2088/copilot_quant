# Contributing to copilot_quant

Thank you for your interest in contributing to copilot_quant! This document provides guidelines for contributing to this project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/harryb2088/copilot_quant.git
   cd copilot_quant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Code Style Guidelines

We use **ruff** for linting and code formatting to maintain consistency across the codebase.

### Running the Linter

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues where possible
ruff check --fix src/ tests/
```

### Style Rules
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write descriptive variable and function names
- Keep functions focused and modular
- Add docstrings to all public functions and classes

## Running Tests

We use pytest for testing. All new features should include corresponding tests.

### Run all tests
```bash
pytest tests/
```

### Run tests with coverage
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

### Run specific test file
```bash
pytest tests/test_data/test_example.py -v
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Ensure all tests pass
   - Run the linter and fix any issues

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure CI checks pass

## Testing Guidelines

- Write tests for all new features
- Maintain or improve code coverage
- Test edge cases and error conditions
- Use meaningful test names that describe what is being tested
- Keep tests isolated and independent

## Project Structure

```
copilot_quant/
├── src/                # Source code
│   ├── data/          # Data ingestion & storage
│   ├── backtest/      # Backtesting engine
│   ├── strategies/    # Trading strategies
│   ├── brokers/       # Broker connectors
│   ├── ui/            # Streamlit UI components
│   └── utils/         # Shared utilities
├── tests/             # Test suite (mirrors src structure)
├── data/              # Local data storage
├── notebooks/         # Jupyter notebooks
└── docs/              # Documentation
```

## Dependency Management

We use **pip-tools** for dependency management:

### Adding a new dependency

1. Add the dependency to `requirements.in`
2. Compile the requirements:
   ```bash
   pip-compile requirements.in
   ```
3. Install the updated requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Code Review

All submissions require code review. We use GitHub pull requests for this purpose. Reviewers will check for:

- Code quality and style
- Test coverage
- Documentation
- Performance considerations
- Security implications

## Questions?

If you have questions about contributing, feel free to open an issue or reach out to the maintainers.

Thank you for contributing to copilot_quant!
