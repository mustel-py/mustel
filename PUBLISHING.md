# Publishing mustel to PyPI

## Prerequisites
- You need a PyPI account: [Register here](https://pypi.org/account/register/)
- You need `twine` installed: `pip install twine`

## 1. Build the Package
(We already did this step!)
```bash
# Clean old builds
rmdir /s /q dist build mustel.egg-info

# Build new version
python -m build
```

## 2. Check the Package (Optional but Recommended)
Run twine check to ensure descriptions render correctly on PyPI.
```bash
twine check dist/*
```

## 3. Upload to TestPyPI (Optional)
Good for testing without affecting the real PyPI.
```bash
twine upload --repository testpypi dist/*
```

## 4. Upload to PyPI (Production)
```bash
twine upload dist/*
```
You will be prompted for your username (usually `__token__`) and your API token.

## 5. Verify
Check the usage page: [https://pypi.org/project/mustel/](https://pypi.org/project/mustel/)
```bash
pip install mustel
```
