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
│  Automation     │
│  Orchestrator   │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────┐   ┌──────────────┐
│  Issue      │   │  Devin       │
│  Processor  │   │  Client      │
└─────────────┘   └──────────────┘
         │                 │
         └────────┬────────┘
                  ▼
         ┌────────────────┐
         │  GitHub Client │
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

### Webhook Mode (Event-Driven)

The automation can be triggered by GitHub webhooks when issues are labeled:

```bash
python webhook_server.py
```

**Workflow:**
1. Engineer adds `devin-remediate` label to an issue
2. GitHub sends webhook event
3. Webhook server receives event and triggers automation
4. Automation adds `devin-in-progress` label
5. Devin processes the issue
6. Automation adds `devin-success` or `devin-failed` label
7. PR-ready comment added if successful

**Setup webhook:**
1. Deploy webhook server (or use ngrok for local testing)
2. Configure GitHub repository webhook:
   - URL: `https://your-server.com/webhook`
   - Content type: `application/json`
   - Events: Issues (specifically label events)
   - Secret: Set `GITHUB_WEBHOOK_SECRET` environment variable

### Manual Mode

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

```bash
docker build -t superset-devin-automation .
docker run --env-file .env superset-devin-automation
```

## Issues Supported

The automation currently handles:

1. **Dependency Upgrades**: Python (Flask) and npm (@deck.gl) package updates
2. **Deprecated Code**: Removal of deprecated classes (SlackNotification)
3. **License Compliance**: Replacing GPL-licensed dependencies (paramiko, pyxlsb)

## Observability

The system provides observability through:
- Console logging with timestamps and session status details
- GitHub comments on each issue with session status and status_detail
- Summary statistics after each run
- Detailed session logs for debugging
- PR-ready comments when Devin creates pull requests for human review
- Status labels for quick visual indication of automation state:
  - `devin-in-progress`: Automation is processing the issue
  - `devin-success`: Automation completed successfully
  - `devin-failed`: Automation failed

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
5. **Add metrics dashboard**: Track automation effectiveness over time
6. **Multi-repo support**: Scale to manage multiple repositories
7. **PR review automation**: Auto-merge PRs that pass CI checks
8. **Label management UI**: Create GitHub Actions to manage labels automatically

## License

Apache License 2.0
