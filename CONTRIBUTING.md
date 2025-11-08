# Contributing to Diamond Painting Generator

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/diamond-painting-generator.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit and push
7. Create a pull request

## Development Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
flutter pub get
```

## Code Style

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints for all functions
- Add docstrings to all public functions and classes
- Format code with `black` and `ruff`

```bash
cd backend
make format
```

### Dart (Frontend)

- Follow Dart style guide
- Use `flutter analyze` to check for issues

```bash
cd frontend
flutter analyze
```

## Testing

### Backend Tests

All new features must include tests.

```bash
cd backend
pytest -v
```

Test coverage should be maintained above 80%.

### Frontend Tests

```bash
cd frontend
flutter test
```

## Pull Request Guidelines

1. **Title**: Use a clear, descriptive title
   - Good: "Add support for custom grid sizes"
   - Bad: "Update code"

2. **Description**: Include:
   - What changes were made
   - Why the changes were necessary
   - How to test the changes
   - Any breaking changes

3. **Tests**: Include tests for new functionality

4. **Documentation**: Update README and docstrings as needed

5. **Commits**: Use clear commit messages
   - Format: `type: description`
   - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
   - Example: `feat: add Bayer dithering algorithm`

## Adding New Features

### Adding a New Palette

1. Edit `backend/palettes.py`:
```python
NEW_PALETTE = ColorPalette(
    name="new_v1",
    colors=[
        ("Color1", "#hex", (r, g, b)),
        # ... exactly 7 colors
    ],
)

PALETTES["new"] = NEW_PALETTE
```

2. Update frontend to include the new style in options

3. Add tests for the new palette

### Adding a New Dithering Algorithm

1. Implement in `backend/pipeline/dither.py`
2. Add to `apply_dithering()` dispatcher
3. Add tests in `tests/test_dither.py`
4. Update API documentation

### Adding Image Preprocessing

1. Implement in `backend/pipeline/preprocess.py`
2. Add to `preprocess_image()` pipeline
3. Add options to `ProcessingOptions` schema
4. Add tests

## Code Review Process

1. All PRs require at least one approval
2. CI tests must pass
3. Code coverage must not decrease
4. Documentation must be updated

## Bug Reports

When filing a bug report, include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Exact steps to reproduce the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, Flutter version
6. **Screenshots**: If applicable

## Feature Requests

When requesting a feature:

1. **Use Case**: Explain why this feature is needed
2. **Proposed Solution**: Describe how it should work
3. **Alternatives**: Other approaches you've considered
4. **Additional Context**: Any other relevant information

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Questions?

If you have questions, please:
1. Check existing issues and documentation
2. Open a discussion on GitHub
3. Ask in the community forum

Thank you for contributing!
