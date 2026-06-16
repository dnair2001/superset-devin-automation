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

- `DEVIN_API_KEY`: Your Devin API key
- `DEVIN_API_URL`: Devin API URL (default: https://api.devin.ai)
- `GITHUB_TOKEN`: GitHub personal access token
- `GITHUB_REPO`: Repository in format "owner/repo"
- `LOG_LEVEL`: Logging level (default: INFO)

## Usage

### Running the Automation

```bash
python automation.py
```

This will:
1. Fetch open issues from the GitHub repository
2. Process each issue with Devin
3. Update GitHub with results
4. Print a summary of the run

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
- Console logging with timestamps
- GitHub comments on each issue with session status
- Summary statistics after each run
- Detailed session logs for debugging

## Example Output

```
==================================================
AUTOMATION SUMMARY
==================================================
Issues Processed: 3
Successful: 2
Failed: 0
Skipped: 1

Session Details:
  Issue #1: completed
  Issue #3: completed
  Issue #4: completed
==================================================
```

## Why Devin

Traditional automation tools (Dependabot, Renovate) can only handle simple, rule-based tasks like version bumps. Devin's unique capabilities enable:

- **Context understanding**: Devin reads and understands code, not just text
- **Complex refactoring**: Can remove deprecated classes and update call sites
- **Legal compliance**: Can research and replace GPL-licensed dependencies
- **Test execution**: Runs tests and fixes failures automatically
- **Natural language instructions**: Describe what you want, not how to do it

## Next Steps

To extend this system for production use:

1. **Add webhook triggers**: Respond to GitHub events in real-time
2. **Implement retry logic**: Handle transient failures gracefully
3. **Add rate limiting**: Respect API rate limits
4. **Expand issue types**: Support more complex refactoring tasks
5. **Add metrics dashboard**: Track automation effectiveness over time
6. **Multi-repo support**: Scale to manage multiple repositories

## License

Apache License 2.0
