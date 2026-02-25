<h1 align="center">
  <br>
  <img src="./docs/images/arbee.png" alt="Arbee" width="200">
  <br>
  Arbee
  <br>
</h1>

<h4 align="center">An automated price arbitrage detection and execution system</h4>

<p align="center">
  <a href="https://github.com/arbeebee/arbee/actions">
    <img src="https://github.com/arbeebee/arbee/actions/workflows/pipeline.yml/badge.svg">
  </a>
</p>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#usage">Usage</a> •
  <a href="#database">Database</a>
</p>

---

## Overview

Arbee is a distributed system designed to detect and execute price arbitrage opportunities across multiple vendor platforms in real-time. The system continuously monitors price discrepancies between vendors and automatically executes transactions when profitable opportunities are identified.

### Key Features

- **Real-time price monitoring** across multiple vendor platforms
- **Automated opportunity detection** using configurable profit thresholds
- **Distributed architecture** for scalability and fault tolerance
- **Transaction execution** with built-in validation rules
- **Notification system** via Telegram for transaction alerts
- **Comprehensive logging** for monitoring and debugging

## Architecture

Arbee implements the [Publisher-Subscriber pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber) with two main components:

### Cloubee (Publisher)

The detection engine responsible for identifying price arbitrage opportunities.

| Responsibility | Implementation |
|----------------|----------------|
| Price scraping | Selenium-based web scraping from Vendor Alpha |
| Price fetching | REST API integration with Vendor Beta |
| Opportunity detection | Real-time price comparison algorithms |
| Message publishing | AWS Simple Notification Service (SNS) |

### Groubee (Subscriber)

The execution engine responsible for acting on detected opportunities.

| Responsibility | Implementation |
|----------------|----------------|
| Message subscription | SNS subscription via ngrok tunnel |
| Transaction execution | Direct API calls to Vendor Alpha |
| Notifications | Telegram bot integration |
| Balance tracking | Google Sheets integration |

### Opportunity Validation

Both components implement validation filters to ensure only viable opportunities are processed:

- Minimum profit thresholds
- Maximum price limits
- Data freshness checks
- Liquidity requirements

## Getting Started

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11.6 |
| pip | 24.3.1+ (with `pyproject.toml` support) |
| Chrome | 126.0.6478.62 |

> **Note:** Chrome can be downloaded from the [official release](http://dl.google.com/release2/chrome/h6yu37x4ixqm357pxq6j7saife_126.0.6478.62/126.0.6478.62_chrome_installer.exe)

### Vendor Alpha Configuration

Before running, configure your Vendor Alpha account with these settings:

| Setting | Value |
|---------|-------|
| Time Zone | AEDT or AEST |
| Max Inactivity Time | 12 Hours |
| Show Balance | ON |
| Skip Confirmation | ON |

### Installation

<details>
<summary><strong>Windows</strong></summary>
<br>

```powershell
# Navigate to project root
cd \path\to\arbee

# Create and activate virtual environment
python -m venv arbee-venv
.\arbee-venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

</details>

<details>
<summary><strong>macOS</strong></summary>
<br>

```zsh
# Navigate to project root
cd ~/path/to/arbee

# Create and activate virtual environment
python -m venv arbee-venv
source ./arbee-venv/bin/activate

# Install dependencies
pip install -r requirements.txt && pip install -e .
```

</details>

### Configuration

#### Environment Variables

1. Copy `.env.template` to `.env`
2. Fill in the required values:

```env
VENDOR_BETA_USER=your_email@example.com
VENDOR_BETA_PASS=your_password
VENDOR_BETA_API_KEY=your_live_api_key
```

<details>
<summary><strong>Obtaining Vendor Beta API Key</strong></summary>
<br>

Arbee requires a **live** API key (not delayed) for real-time price data.

1. Register for a developer account with Vendor Beta
2. Create an application to generate API keys
3. Request activation of the live API key (verification may be required)
4. Verify the API key is active before use

</details>

<details>
<summary><strong>Setting up Telegram Notifications</strong></summary>
<br>

**Step 1: Create a Telegram Bot**

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Save the HTTP API token provided (e.g., `63xxxxxx71:AAFoxxxxn0hwA-2TVSxxxNf4c`)

**Step 2: Get Your Chat ID**

1. Start a conversation with your new bot
2. Send any message
3. Visit `https://api.telegram.org/bot{YOUR_TOKEN}/getUpdates`
4. Find the `chat.id` value in the JSON response

**Step 3: Configure Environment**

```env
TELEGRAM_AUTH_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

</details>

<details>
<summary><strong>Setting up ngrok</strong></summary>
<br>

1. Sign up at [ngrok.com](https://dashboard.ngrok.com/signup)
2. Copy your auth token from the [dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)
3. Add to `.env`:

```env
NGROK_AUTHTOKEN=your_auth_token
```

</details>

<details>
<summary><strong>Setting up Google Sheets Integration</strong></summary>
<br>

1. Add to `.env`:

```env
TRACKER_FILE_ID=your_google_sheets_id
MACHINE=your_machine_name
```

2. Obtain credentials from the project administrator and place at `/secrets/credentials.json`

</details>

<details>
<summary><strong>AWS Credentials</strong></summary>
<br>

Contact the project administrator for AWS account provisioning and credentials.

</details>

## Usage

### Running the Components

**Using launch scripts (recommended):**

```bash
# Scripts are located in ./scripts/
./scripts/macos-run-cloubee.sh  # or windows equivalent
./scripts/macos-run-groubee.sh
```

**Running directly:**

```bash
# Start the detection engine
python ./src/cloubee/main.py

# Start the execution engine
python ./src/groubee/main.py
```

### Automated Scheduling

<details>
<summary><strong>Windows Task Scheduler</strong></summary>
<br>

**Prerequisites:**
1. [Disable Fast Startup](https://help.uaudio.com/hc/en-us/articles/213195423-How-To-Disable-Fast-Startup-in-Windows)
2. [Enable auto-login](https://support.lenovo.com/au/en/solutions/ht503518-how-to-remove-login-password-from-windows-10)

**Create startup script** (`arbee-launcher.bat`):

```bat
@echo off

for /f "tokens=1-4 delims=:. " %%A in ("%time%") do (
    set hour=%%A
)

if %hour% GEQ 17 (
    echo Starting Arbee...
    schtasks /create /sc once /tn "Scheduled Shutdown" /tr "shutdown /s /f /t 0" /st 07:10

    cd /d C:\path\to\arbee
    call .\arbee-venv\Scripts\activate
    python .\src\groubee\main.py
) else (
    echo Skipping - before 5 PM
)

timeout /t 30 >nul
```

**Configure Task Scheduler:**

1. Create a new task triggered on user login
2. Set a delay (30-60 seconds) for system startup
3. Disable AC power and wake requirements
4. Configure BIOS for daily 5 PM startup

</details>

<details>
<summary><strong>macOS</strong></summary>
<br>

> **Note:** Mac must be connected to a power source

**1. Enable auto-login:**

System Preferences > Users & Groups > Automatically log in as: [your user]

**2. Schedule startup:**

System Preferences > Battery > Schedule > Start up or wake > Everyday at 5PM

**3. Configure cron job:**

```bash
crontab -e
# Add: 10 17 * * * cd /path/to/arbee && ./scripts/macos-run-groubee.sh
```

**4. Prevent sleep:**

```bash
sudo pmset -a disablesleep 1
```

**5. Schedule shutdown:**

```bash
# Allow passwordless shutdown
sudo visudo
# Add: your_username ALL=(ALL) NOPASSWD: /sbin/shutdown

# Add cron job
crontab -e
# Add: 0 5 * * * sudo /sbin/shutdown -h now
```

</details>

### Logging

Logs are written to the `/logs` directory (git-ignored). Log files are cleared on each run.

### Testing

Tests run automatically on push via CI/CD. To run locally:

```bash
pytest
```

### Terminating Chrome Processes

If Chrome processes become stuck:

```bash
# Windows
taskkill /F /IM chrome.exe

# macOS
pkill -f "Google Chrome"
```

## Database

### Connecting to AWS Database

1. Install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
2. Install [Session Manager Plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
3. Configure credentials: `aws configure`
4. Start port forwarding: `python db_proxy.py`
5. Connect via [pgweb](https://sosedoff.github.io/pgweb/): `pgweb --ssl=require`

### Migrations

This project uses **Alembic** for database migrations with timestamped revision IDs.

| Command | Description |
|---------|-------------|
| `make migration-create MESSAGE="description"` | Create a new migration |
| `make migration-upgrade` | Apply pending migrations |
| `make migration-downgrade` | Revert the latest migration |
| `make migration-current` | Show current revision |
| `make migration-history` | Show migration history |

**Example:**

```bash
make migration-create MESSAGE="add-foreign-key"
# Creates: migrations/versions/202504011935_add_foreign_key.py
```
