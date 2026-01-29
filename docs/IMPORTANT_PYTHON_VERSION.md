# IMPORTANT: Python Version for Apple Silicon Macs

## Issue Found

If you have **Anaconda** installed, the default `python3` command may use the **x86_64 (Intel) version** running under Rosetta, which causes PyAudio installation issues.

## Solution

**Always use the native ARM64 Python from Homebrew:**

```bash
# Use this Python (native ARM64)
/opt/homebrew/bin/python3.11

# NOT this (Anaconda x86_64)
/Users/kid/opt/anaconda3/bin/python3
```

## Your Virtual Environment

The `venv` directory has been created with the correct Python:
- **Python Version:** 3.11.14
- **Architecture:** ARM64 (native Apple Silicon)
- **Location:** `/opt/homebrew/bin/python3.11`

## How to Activate

```bash
source venv/bin/activate
```

## Verify Your Python

Check which Python is being used:

```bash
source venv/bin/activate
python --version
file $(which python)
```

Should show:
- Python 3.11.x
- Mach-O 64-bit executable **arm64**

## If You Recreate the Virtual Environment

Always use the Homebrew Python:

```bash
# Delete old venv
rm -rf venv

# Create new venv with correct Python
/opt/homebrew/bin/python3.11 -m venv venv

# Activate and install
source venv/bin/activate
pip install -r requirements.txt
```

## Summary

✅ **Current setup:** Using native ARM64 Python - everything works!
❌ **Anaconda Python:** Causes PyAudio architecture mismatch errors

---

**Note:** This is only relevant for Apple Silicon Macs (M1/M2/M3). Intel Macs don't have this issue.
