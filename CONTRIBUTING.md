# Contributing

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[full,dev,build]
pytest
```

On Windows, activate the virtual environment with:

```powershell
.venv\Scripts\activate
```

## Code rules

- Keep conversion logic inside backends or `ConverterService`.
- Keep GUI logic out of backend classes.
- Never hard-code a format as supported unless the active backend can actually read/write it.
- Add tests for every conversion or path-discovery behavior change.
- Do not commit large vendor binaries unless release licensing has been verified.
