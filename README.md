# Superset Devin Automation

Event-driven automation system that uses Devin AI to automatically remediate GitHub issues in the Apache Superset repository.

## Overview

This system demonstrates how Devin can be used as a core primitive to build automated workflows that:
- Monitor GitHub repositories for open issues
- Categorize issues by type (dependency upgrades, deprecated code, license compliance)
- Generate remediation plans using natural language instructions
- Execute fixes using Devin's autonomous coding capabilities
- Provide observability through logging and GitHub status updates

## Problem Solved

Engineering teams spend significant time on repetitive maintenance tasks:
- **Dependency upgrades**: Updating packages, regenerating requirements, running tests
- **Deprecated code removal**: Removing old APIs, updating call sites
- **License compliance**: Identifying and replacing incompatible dependencies

This automation reduces toil and allows engineers to focus on higher-value work.

## Architecture

```
┌─────────────────┐
│  GitHub Issues  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GitHub Webhook │
│     Event       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Webhook Server │
│  (Flask)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Automation     │
│  Orchestrator   │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────┐   ┌──────────────┐
│  GitHub     │   │  Devin       │
│  Client     │   │  Client      │
└─────────────┘   └──────────────┘
         │                 │
         └────────┬────────┘
                  ▼
         ┌────────────────┐
         │  Label Mgmt &   │
         │  Observability │
         └────────────────┘
```

## Setup

### Prerequisites

- Python 3.11+
- Devin API key
- GitHub personal access token
- Fork of Apache Superset repository

### Installation

1. Clone this repository:
```bash
git clone https://github.com/dnair2001/superset-devin-automation.git
cd superset-devin-automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

- `DEVIN_API_KEY`: Your Devin API v3 key
- `DEVIN_ORG_ID`: Your Devin organization ID
- `DEVIN_API_URL`: Devin API URL (default: https://api.devin.ai)
- `GITHUB_TOKEN`: GitHub personal access token
- `GITHUB_REPO`: Repository in format "owner/repo"
- `DEVIN_GITHUB_SECRET_ID`: (Optional) Devin secret ID for GitHub authentication
- `GITHUB_WEBHOOK_SECRET`: (Optional) Secret for webhook signature verification
- `WEBHOOK_PORT`: Port for webhook server (default: 5000)
- `LOG_LEVEL`: Logging level (default: INFO)
- `DEMO_MODE`: Set to "true" to run in demo mode without real Devin sessions

## Usage

### Webhook Mode (Event-Driven) - Recommended

The automation is designed to be event-driven, triggered by GitHub webhooks when issues are labeled:

```bash
python webhook_server.py
```

**Workflow:**
1. Engineer adds `devin-remediate` label to an issue
2. GitHub sends webhook event to webhook server
3. Webhook server verifies signature and triggers automation
4. Automation adds `devin-in-progress` label
5. Devin processes the issue
6. Automation adds `devin-success` or `devin-failed` label
7. PR-ready comment added if successful

**Webhook Features:**
- Signature verification for security
- Label-based state machine to prevent duplicate processing
- Protection against webhook loops
- Handles GitHub webhooks that don't send label changes structure

**Setup webhook:**
1. Deploy webhook server (or use ngrok for local testing)
2. Configure GitHub repository webhook:
   - URL: `https://your-server.com/webhook`
   - Content type: `application/json`
   - Events: Issues (specifically label events)
   - Secret: (OPTIONAL) Set `GITHUB_WEBHOOK_SECRET` environment variable

**Local testing with ngrok:**
```bash
# Start webhook server
WEBHOOK_PORT=5001 python webhook_server.py

# In another terminal, start ngrok
ngrok http 5001

# Use the ngrok URL for GitHub webhook configuration
```

### Manual Mode

For manual execution without webhooks:

```bash
python automation.py
```

This will:
1. Fetch open issues from the GitHub repository
2. Process each issue with Devin
3. Wait for sessions to complete (using v3 API status_detail field)
4. Add PR-ready comments when Devin creates a PR and waits for human review
5. Update GitHub with results
6. Print a summary of the run

### Demo Mode

For testing or demonstration purposes, you can run in demo mode without making real Devin API calls:

```bash
python automation.py --demo
```

Or set the environment variable:
```bash
export DEMO_MODE=true
python automation.py
```

### Running with Docker

**Webhook Mode (Recommended):**
```bash
# Build the Docker image
docker build -t superset-devin-automation .

# Run the webhook server
docker run --env-file .env -p 5001:5001 superset-devin-automation
```

The webhook server will be available at `http://localhost:5001` with endpoints:
- `/webhook` - GitHub webhook endpoint
- `/metrics` - JSON metrics API
- `/dashboard` - HTML metrics dashboard

**Testing the Webhook with Docker:**

To test the GitHub webhook integration locally:

1. **Start the Docker container** (as shown above)

2. **Set up ngrok** to expose the container to GitHub:
   ```bash
   ngrok http 5001
   ```

3. **Configure GitHub webhook** in your repository settings under "Webhook":
   - URL: Use the ngrok URL (e.g., `https://your-ngrok-url.ngrok-free.dev/webhook`)
   - Content type: `application/json`
   - Events: Issues (specifically label events)
   - Secret: (Optional) Set `GITHUB_WEBHOOK_SECRET` in your `.env` file for signature verification

4. **Test the automation** by adding the `devin-remediate` label to any issue in your GitHub repository

5. **Monitor the logs** in the Docker container to see the webhook events and automation execution

**Alternative: Demo Mode (No API Keys Required)**
```bash
# Build the Docker image
docker build -t superset-devin-automation .

# Run in demo mode
docker run --env-file .env -e DEMO_MODE=true -p 5001:5001 superset-devin-automation
```

Demo mode simulates the workflow without making real Devin API calls, useful for testing the webhook logic without API costs.

**Manual Mode:**
```bash
# Build the Docker image
docker build -t superset-devin-automation .

# Run manual automation
docker run --env-file .env superset-devin-automation python automation.py
```

## Issues Supported

The automation currently handles:

1. **Dependency Upgrades**: Python (Flask) and npm (@deck.gl) package updates
2. **Deprecated Code**: Removal of deprecated classes (SlackNotification)
3. **License Compliance**: Replacing GPL-licensed dependencies (paramiko, pyxlsb)

## Observability

The system provides comprehensive observability through multiple channels:

### Metrics Dashboard

**HTML Dashboard:**
- Access at `http://localhost:5001/dashboard` (or via ngrok)
- Visual display of key metrics in a clean, user-friendly interface
- Real-time updates when page is refreshed
- Color-coded success/failure indicators

**JSON Metrics API:**
- Access at `http://localhost:5001/metrics`
- Programmatic access to metrics for monitoring tools
- Returns JSON with current automation statistics

**Metrics tracked:**
- Total processed issues
- Successful vs failed counts
- Success rate percentage
- Active sessions
- Average processing time

### GitHub Integration

- **Status labels** for quick visual indication:
  - `devin-in-progress`: Automation is processing the issue
  - `devin-success`: Automation completed successfully
  - `devin-failed`: Automation failed
- **GitHub comments** on each issue with session status and status_detail
- **PR-ready comments** when Devin creates pull requests for human review

### Logging

- Console logging with timestamps and session status details
- Detailed session logs for debugging
- Summary statistics after each run

### Label-Based State Machine

The automation uses a label-based state machine to prevent duplicate processing:
- Only triggers when `devin-remediate` is added to an issue
- Skips if issue already has `devin-in-progress` (already processing)
- Skips if issue already has `devin-success` or `devin-failed` (already completed)
- Prevents webhook loops and duplicate Devin sessions

## Session Completion Detection

The automation uses the Devin API v3 `status_detail` field to detect when sessions are complete. This is necessary because in v3 API, the `status` field can remain "running" even when the task is complete. The automation treats the following `status_detail` values as completion states:

- `waiting_for_user`: Devin has created a PR and is waiting for human review (adds PR-ready comment, does not close issue)
- `finished`: Task is fully complete (closes issue)
- `failed`: Task failed (adds failure comment with logs)
- `cancelled`: Task was cancelled (adds failure comment)

This approach prevents timeout errors and ensures accurate detection of session completion.

## Example Output

```
==================================================
AUTOMATION SUMMARY
==================================================
Issues Processed: 3
Successful: 3
Failed: 0
Skipped: 0

Session Details:
  Issue #3: waiting_for_user
  Issue #4: waiting_for_user
  Issue #5: waiting_for_user
==================================================
```

When sessions reach `waiting_for_user` status, the automation adds a PR-ready comment:
```
🔄 PR is ready to remediate this issue. Waiting for human review on PR.

Session: 2a72c7df0d724bec93b7a7bca42d4b6e
Status: waiting_for_user
```

## Why Devin

Traditional automation tools (Dependabot, Renovate) can only handle simple, rule-based tasks like version bumps. Devin's unique capabilities enable:

- **Context understanding**: Devin reads and understands code, not just text
- **Complex refactoring**: Can remove deprecated classes and update call sites
- **Legal compliance**: Can research and replace GPL-licensed dependencies
- **Test execution**: Runs tests and fixes failures automatically
- **Natural language instructions**: Describe what you want, not how to do it

## Technical Details

### Devin API v3 Integration

The automation uses the Devin API v3 endpoints:
- `POST /v3/organizations/{org_id}/sessions` - Create new sessions
- `GET /v3/organizations/{org_id}/sessions/{session_id}` - Get session status

Key differences from v1/v2:
- Requires organization ID in the URL path
- Uses `prompt` field for instructions instead of `instructions`
- Uses `repos` array instead of `repository` string
- Session completion is determined by `status_detail` field, not `status`

### GitHub Authentication

The automation supports GitHub authentication through Devin secrets:
1. Create a secret in Devin with your GitHub token
2. Pass the secret ID via `DEVIN_GITHUB_SECRET_ID` environment variable
3. Devin uses this secret to push changes to your repository

This allows Devin to create pull requests without exposing your GitHub credentials in the automation code.

## Next Steps

To extend this system for production use:

1. **Deploy webhook server**: Use cloud hosting (Heroku, AWS, etc.) for webhook server
2. **Implement retry logic**: Handle transient failures gracefully
3. **Add rate limiting**: Respect API rate limits
4. **Expand issue types**: Support more complex refactoring tasks
5. **Multi-repo support**: Scale to manage multiple repositories
6. **PR review automation**: Auto-merge PRs that pass CI checks
7. **Label management UI**: Create GitHub Actions to manage labels automatically
8. **Advanced metrics**: Historical trends, performance analytics, alerting
9. **SLA monitoring**: Alert on long-running sessions or high failure rates
10. **Security scanning integration**: Trigger on security tool findings

## License

Apache License 2.0
