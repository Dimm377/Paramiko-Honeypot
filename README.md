# 🍯 SSH Honeypot

Simple SSH honeypot using Paramiko to capture login credentials.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python Honeypot.py
```

## Test ssh

```bash
ssh -p 2222 test@localhost
```

## Log

Credentials tersimpan di `honeypot.log`:

```
🔑 AUTH ATTEMPT - IP: @localhost | User: test | Pass: anjirlah gabisa login
```

## ⚠️ Disclaimer

For educational purpose only.
