# Hatchet Workflow Registration Guide

## Overview

The loan underwriting system uses **Hatchet** for workflow orchestration. The workflow is defined in code but must be **registered** with Hatchet Cloud before it can be used.

## How It Works

1. **Workflow Definition**: [backend/app/workflows/underwriting_workflow.py](backend/app/workflows/underwriting_workflow.py) defines the `underwriting-workflow` with 6 steps
2. **Worker Registration**: A Hatchet worker connects to Hatchet Cloud and registers the workflow
3. **Job Execution**: When the API triggers underwriting, Hatchet Cloud dispatches jobs to the worker

## Registration Methods

### Option 1: Docker Compose (Recommended)

The easiest way is to use the included `hatchet-worker` service:

```bash
# Make sure HATCHET_CLIENT_TOKEN is in your .env file
docker-compose up -d hatchet-worker

# Check worker logs
docker logs -f loan-underwriting-hatchet-worker
```

You should see:
```
✅ Workflow registered successfully
👂 Worker listening for jobs...
```

### Option 2: Local Python

Run the worker locally for development:

```bash
cd backend

# Make sure token is exported
export HATCHET_CLIENT_TOKEN="your_token_here"

# Run the worker
python worker.py
```

## Verification

### 1. Check Worker Status

```bash
# Docker
docker logs loan-underwriting-hatchet-worker

# Look for:
# ✅ Workflow registered successfully
```

### 2. Trigger Underwriting

```bash
curl -X POST http://localhost:8001/api/v1/underwriting/{application_id}/run
```

### 3. Check API Logs

```bash
docker logs loan-underwriting-api | grep Hatchet

# Success looks like:
# ℹ️ Attempting to use Hatchet for application {id}
# ✓ Started Hatchet workflow {workflow_run_id} for application {reference_id}

# Failure (if worker not running):
# ✗ Hatchet workflow failed, falling back to BackgroundTasks
```

## Troubleshooting

### "workflow names not found: underwriting-workflow"

**Cause**: Worker is not running or hasn't registered the workflow  
**Fix**: Start the worker using one of the methods above

### "HATCHET_CLIENT_TOKEN not set"

**Cause**: Token missing from environment  
**Fix**: Add to `.env` file:
```bash
HATCHET_CLIENT_TOKEN=your_token_from_hatchet_cloud
```

### Worker starts but workflow doesn't trigger

**Cause**: API and worker might be using different Hatchet tenants  
**Fix**: Ensure both use the same `HATCHET_CLIENT_TOKEN`

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   FastAPI       │────▶│  Hatchet Cloud   │────▶│   Worker    │
│   (Trigger)     │     │  (Orchestrator)  │     │ (Executor)  │
└─────────────────┘     └──────────────────┘     └─────────────┘
         │                                               │
         │         If Hatchet unavailable               │
         ▼                                               ▼
  ┌──────────────┐                              ┌────────────┐
  │BackgroundTask│                              │  Database  │
  │  (Fallback)  │──────────────────────────────▶│            │
  └──────────────┘                              └────────────┘
```

## Production Deployment

For production, you have two options:

### Option A: Keep Worker Running
- Deploy the worker as a separate service (Docker container, systemd, etc.)
- Ensure it has database access and the same environment variables
- Worker will continuously listen for jobs

### Option B: Use BackgroundTasks
- If you don't want to manage a separate worker process
- The system already falls back to FastAPI BackgroundTasks
- Works identically but without Hatchet's dashboard and monitoring

## Hatchet Dashboard

Once registered, you can monitor workflows at:
- **URL**: https://cloud.onhatchet.run
- **Features**:
  - View workflow runs in real-time
  - See step-by-step execution
  - Debug failed steps
  - Retry failed workflows

## Token Management

Get your Hatchet token from:
1. Sign up at https://cloud.onhatchet.run
2. Create a new tenant (or use default)
3. Go to Settings → API Tokens
4. Generate a new token
5. Add to `.env` file

## Status Summary

✅ **Current State**:
- Workflow defined in code
- API triggers with Hatchet-first approach
- Graceful fallback to BackgroundTasks
- Worker service configured in docker-compose.yml

⏳ **To Enable Hatchet**:
- Start the worker: `docker-compose up -d hatchet-worker`
- Verify registration in logs
- Test with an underwriting run