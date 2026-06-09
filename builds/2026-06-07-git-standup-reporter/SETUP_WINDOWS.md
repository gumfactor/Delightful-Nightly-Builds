# Windows Setup — Git Standup Reporter

> **Version:** 2.0 (2026-06-08)

## Requirements

- Python 3.11 or later (for `tomllib` support)
- Git for Windows
- A GitHub personal access token (read-only `repo` scope)

---

## Step 1 — Create a GitHub Token

1. Go to github.com → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Click **Generate new token (classic)**
3. Set expiry (90 days recommended; you'll need to renew it)
4. Check the **`repo`** scope (needed for private repos; use `public_repo` if you only have public repos)
5. Copy the token — you won't see it again

---

## Step 2 — Set the GITHUB_TOKEN Environment Variable

Open PowerShell as Administrator:

```powershell
[System.Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "your-token-here", "User")
```

This sets it permanently for your user. Restart any open terminals for it to take effect.

---

## Step 3 — Configure standup.toml

Copy `standup.toml.example` to `standup.toml` in the same folder:

```toml
[standup]
github_username = "gumfactor"
hours = 24
format = "markdown"
journal_path = "C:/Users/yourname/.standup_journal.jsonl"
local_roots = ["C:/Dev"]
exclude_repos = []
```

Replace `yourname` with your Windows username. The journal file will be created automatically.

---

## Step 4 — Test It Manually

Open a terminal, navigate to the build folder, and run:

```powershell
python main.py
```

You should see a standup report. If you see "GITHUB_TOKEN not set", reopen the terminal after setting the variable in Step 2.

---

## Step 5 — Schedule with Task Scheduler

Run this PowerShell command to create a daily 7am task (adjust the path to match where your build lives):

```powershell
$action = New-ScheduledTaskAction `
    -Execute "python" `
    -Argument "C:\path\to\builds\2026-06-07\main.py >> C:\Users\yourname\.standup_today.md 2>&1" `
    -WorkingDirectory "C:\path\to\builds\2026-06-07"

$trigger = New-ScheduledTaskTrigger -Daily -At 7am

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "GitStandupReporter" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Limited `
    -Force
```

This appends the day's report to `C:\Users\yourname\.standup_today.md` each morning. Open that file at the start of your day.

To run the task immediately (to test):

```powershell
Start-ScheduledTask -TaskName "GitStandupReporter"
```

To remove the task:

```powershell
Unregister-ScheduledTask -TaskName "GitStandupReporter" -Confirm:$false
```

---

## Running Tests

```powershell
python -m pytest tests/ -v
```

Expected: all tests pass. The GitHub API tests use mocked responses and make no real network calls.
