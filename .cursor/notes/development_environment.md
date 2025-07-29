# Development Environment

## ⚠️ ALWAYS USE VIRTUAL ENVIRONMENT ⚠️

**CRITICAL REMINDER**: Always activate the virtual environment before working on this project!

### Setup

The project has a `.venv/` directory containing the virtual environment.

### Activation

```bash
source .venv/bin/activate
```

### Verification

After activation, verify you're using the venv python:

```bash
which python
# Should show: /path/to/project/.venv/bin/python
# NOT: /usr/bin/python
```

### Dependencies Installation

Always install dependencies inside the activated virtual environment:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Why Virtual Environment is Required

1. **Isolated Dependencies**: Prevents conflicts with system Python packages
2. **Reproducible Environment**: Ensures consistent dependency versions
3. **Clean Development**: Avoids polluting system Python installation
4. **Project Portability**: Other developers can replicate exact environment

### Project Dependencies

- `beautifulsoup4` - HTML parsing
- `selenium` - Browser automation
- `webdriver-manager` - Chrome driver management
- `pytest` - Testing framework
- `PyPDF2` - PDF text extraction (for document processing)
- `requests` - HTTP requests (for PDF downloads)

## Poetry Alternative

The project also supports Poetry package management:

```bash
poetry install
poetry shell  # Activates poetry venv
```

## Important Notes

- **Never run pip commands without activating venv first**
- Check `which python` before installing packages
- The `.venv/` directory should not be committed to git
- Always document new dependencies in `requirements.txt`
