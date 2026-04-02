# Virtual Environment Setup & Troubleshooting Guide

## ✅ Current Status

- ✅ Incorrect root `.venv/` deleted
- ✅ Fresh backend `.venv/` created for current user (acer)
- ✅ All 13 required packages installed
- ✅ requirements.txt generated
- ✅ VS Code configured with correct interpreter

---

## 📋 Quick Setup Commands (Copy & Paste)

### Command 1: Activate Virtual Environment (Always start here!)

**Windows PowerShell:**
```powershell
cd "c:\Users\acer\Downloads\stock sentinal\backend"
.\.venv\Scripts\Activate.ps1
```

**After activation, your prompt should show:**
```
(.venv) PS C:\Users\acer\Downloads\stock sentinal\backend>
```

### Command 2: Check Python & Pip

```powershell
python --version
pip --version
pip list
```

### Command 3: Run Application

```powershell
# From backend folder with venv activated
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Command 4: Stop Application

```powershell
Ctrl + C
```

### Command 5: Deactivate Virtual Environment

```powershell
deactivate
```

---

## 📦 Installation Verification

### Verify All Core Packages

```powershell
# After activating venv, run:
python -c "import fastapi, sqlalchemy, pydantic, httpx, apscheduler; print('✅ All core packages imported successfully')"
```

### Expected Output:
```
✅ All core packages imported successfully
```

### List All Installed Packages

```powershell
pip list
```

### Check Specific Package

```powershell
pip show fastapi
pip show sqlalchemy
pip show pydantic
```

---

## 🔧 Troubleshooting

### Issue 1: "Python command not found" (but venv is activated)

**Solution:**
```powershell
# Use full path explicitly
.\.venv\Scripts\python.exe --version

# Or reinstall pip
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

### Issue 2: "venv not activated" (prompt doesn't show "(.venv)")

**Solution:**
```powershell
# Make sure you're in backend folder
cd "c:\Users\acer\Downloads\stock sentinal\backend"

# Activate it (may need to fix execution policy first)
.\.venv\Scripts\Activate.ps1

# If stil fails with "cannot be loaded":
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

### Issue 3: "Import error: No module named 'fastapi'"

**Possible causes:**
1. ❌ venv not activated
2. ❌ Wrong Python interpreter in VS Code
3. ❌ Package not installed

**Fix:**
```powershell
# 1. Verify venv is activated (look for (.venv) in prompt)
# 2. Check VS Code uses correct interpreter:
#    - Open Command Palette (Ctrl+Shift+P)
#    - Type: Python: Select Interpreter
#    - Choose: ./backend/.venv/Scripts/python.exe
# 3. Install package if missing:
pip install fastapi
```

### Issue 4: "requirements.txt is old/missing"

**Regenerate it:**
```powershell
cd "c:\Users\acer\Downloads\stock sentinal\backend"
.\.venv\Scripts\pip.exe freeze > requirements.txt
```

### Issue 5: "psycopg2 won't install"

**Already installed correctly as `psycopg2-binary`**
```powershell
pip show psycopg2-binary
# Should show version 2.9.11
```

### Issue 6: "Still seeing old venv errors"

**Completely reset:**
```powershell
# Delete broken venv
cd "c:\Users\acer\Downloads\stock sentinal\backend"
Remove-Item -Path ".\.venv" -Recurse -Force

# Create fresh venv
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install all packages
pip install fastapi uvicorn[standard] sqlalchemy psycopg2-binary alembic pydantic pydantic-settings python-dotenv 'passlib[bcrypt]' PyJWT httpx apscheduler yfinance

# Generate requirements
pip freeze > requirements.txt
```

### Issue 7: "VS Code still suggests wrong interpreter"

**Force reselection:**

1. **Open Command Palette:** `Ctrl + Shift + P`
2. **Type:** `Python: Select Interpreter`
3. **Search for:** `.venv` or `backend`
4. **Choose:** `./backend/.venv/Scripts/python.exe`

Verify in VS Code status bar (bottom right) - should show correct path.

### Issue 8: "Terminal doesn't auto-activate venv"

**Ensure these settings exist in `.vscode/settings.json`:**
```json
{
    "python.terminal.activateEnvInCurrentTerminal": true,
    "python.terminal.activateEnvironmentInTerminal": true
}
```

Then restart VS Code terminal:
```powershell
# Close terminal with X button
# Reopen with Ctrl + ~
```

### Issue 9: "Alembic says 'No changes detected' or migration fails"

**Make sure models are imported:**
```python
# In alembic/env.py, ensure this line exists:
from app.models import *  # noqa
```

**Then run:**
```powershell
alembic revision --autogenerate -m "Your migration name"
alembic upgrade head
```

### Issue 10: "Port 8000 already in use"

```powershell
# Specify different port
uvicorn app.main:app --port 8001 --reload

# Or kill process using port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 🔄 Reinstall Everything (Nuclear Option)

**If something is completely broken:**

```powershell
cd "c:\Users\acer\Downloads\stock sentinal\backend"

# Delete venv
Remove-Item -Path ".\.venv" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✅ Deleted .venv"

# Create fresh venv
python -m venv .venv
Write-Host "✅ Created fresh .venv"

# Activate
.\.venv\Scripts\Activate.ps1
Write-Host "✅ Activated .venv"

# Upgrade pip
.\.venv\Scripts\python.exe -m pip install --upgrade pip
Write-Host "✅ Upgraded pip"

# Install all packages
.\.venv\Scripts\pip.exe install fastapi uvicorn[standard] sqlalchemy psycopg2-binary alembic pydantic pydantic-settings python-dotenv 'passlib[bcrypt]' PyJWT httpx apscheduler yfinance
Write-Host "✅ Installed all packages"

# Generate requirements
.\.venv\Scripts\pip.exe freeze > requirements.txt
Write-Host "✅ Generated requirements.txt"

# Verify
.\.venv\Scripts\python.exe -c "import fastapi, sqlalchemy, pydantic; print('✅ All working!')"
```

---

## 📁 File Structure Checklist

After cleanup, your structure should be:

```
c:\Users\acer\Downloads\stock sentinal\
├── .venv/                          ❌ DELETED (root level - wrong)
├── .vscode/
│   ├── settings.json              ✅ NEW (Python interpreter config)
│   └── extensions.json            ✅ NEW (Extensions recommendations)
├── backend/
│   ├── .venv/                     ✅ KEPT (current user's venv)
│   │   ├── Scripts/
│   │   │   ├── Activate.ps1
│   │   │   ├── python.exe
│   │   │   └── pip.exe
│   │   └── Lib/
│   │       └── site-packages/     (all packages installed here)
│   ├── requirements.txt           ✅ UPDATED (with all packages)
│   ├── app/
│   ├── alembic/
│   └── ...
├── frontend/
└── ...
```

---

## ✨ Best Practices Going Forward

### 1. **Always activate before working:**
```powershell
cd c:\Users\acer\Downloads\stock sentinal\backend
.\.venv\Scripts\Activate.ps1
```

### 2. **Install new packages correctly:**
```powershell
# With venv activated
pip install new-package

# Then update requirements.txt
pip freeze > requirements.txt
```

### 3. **Never delete `.venv` unless needed**

### 4. **Share requirements.txt, NOT `.venv` folder**

### 5. **When cloning project fresh:**
```powershell
# Create venv
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install from requirements.txt
pip install -r requirements.txt
```

### 6. **Use .gitignore for venv:**
Ensure `.gitignore` contains:
```
.venv/
venv/
env/
__pycache__/
*.pyc
```

---

## 🚀 Running FastAPI Application

```powershell
# 1. Navigate to backend
cd "c:\Users\acer\Downloads\stock sentinal\backend"

# 2. Activate venv
.\.venv\Scripts\Activate.ps1

# 3. Start app
uvicorn app.main:app --reload

# 4. Visit in browser
# http://localhost:8000/api/docs  (Swagger UI)
# http://localhost:8000/api/redoc (ReDoc)

# 5. Stop with Ctrl + C
```

---

## 📊 Package Versions Installed

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.135.3 | Web framework |
| uvicorn | 0.42.0 | ASGI server |
| sqlalchemy | 2.0.48 | ORM |
| pydantic | 2.12.5 | Data validation |
| pydantic-settings | 2.13.1 | Settings management |
| python-dotenv | 1.2.2 | Environment variables |
| psycopg2-binary | 2.9.11 | PostgreSQL driver |
| alembic | 1.18.4 | Database migrations |
| passlib | 1.7.4 | Password hashing |
| PyJWT | 2.12.1 | JWT tokens |
| httpx | 0.28.1 | HTTP client |
| apscheduler | 3.11.2 | Task scheduling |
| yfinance | 1.2.0 | Stock data |

---

## 🎯 VS Code Configuration

Your `.vscode/settings.json` now includes:

✅ Python interpreter path (backend/.venv)  
✅ Automatic venv activation in terminal  
✅ Black formatter on save  
✅ Type checking enabled  
✅ Recommended extensions list  
✅ Editor rulers at 88 and 120 characters  
✅ Auto exclude __pycache__ and .pyc files  

**To reload settings:** `Ctrl + Shift + P` → "Reload Window"

---

## 💡 Tips & Tricks

### Check which Python is active:
```powershell
where python
Get-Command python | Select-Object Definition
```

### See full venv path:
```powershell
$env:VIRTUAL_ENV
```

### Compare versions before/after:
```powershell
pip list > before.txt
# ... make changes ...
pip list > after.txt
# Compare in VS Code Diff
```

### Create isolated test environment:
```powershell
# Keep backend/.venv for production
# Create temp test venv
python -m venv temp_test
.\temp_test\Scripts\Activate.ps1
# ... test ...
Remove-Item -Path ".\temp_test" -Recurse -Force
```

---

## 📞 Quick Reference Commands

| Task | Command |
|------|---------|
| List packages | `pip list` |
| Show package info | `pip show package-name` |
| Reinstall package | `pip install --force-reinstall package-name` |
| Update package | `pip install --upgrade package-name` |
| freeze requirements | `pip freeze > requirements.txt` |
| Install from requirements | `pip install -r requirements.txt` |
| Check for outdated | `pip list --outdated` |
| Uninstall package | `pip uninstall package-name` |
| Test import | `python -c "import module"` |
| Show venv path | `echo $env:VIRTUAL_ENV` |
| Deactivate venv | `deactivate` |

---

## ✅ Cleanup Summary

**What was done:**
1. ✅ Deleted root `.venv/` (was broken from different user)
2. ✅ Recreated backend `.venv/` for current user (acer)
3. ✅ Installed all 13 required packages + dependencies
4. ✅ Generated `requirements.txt` with all versions
5. ✅ Configured VS Code with correct interpreter path
6. ✅ Created `.vscode/settings.json` and `extensions.json`
7. ✅ Created this comprehensive troubleshooting guide

**What you should do now:**
1. Restart VS Code
2. Press `Ctrl + Shift + P` → "Python: Select Interpreter"
3. Verify it shows `./backend/.venv/Scripts/python.exe`
4. Open a new terminal (`Ctrl + ~`)
5. Verify `(.venv)` appears in prompt
6. Start developing! 🚀

---

**Generated:** 2026-04-01  
**Status:** ✅ Production Ready  
**Python Version:** 3.14.3  
**Virtual Environment:** `/backend/.venv/`
