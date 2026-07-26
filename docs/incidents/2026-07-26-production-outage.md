# Production Outage: Expired Database + Stale API Keys

Date discovered: 2026-07-26
Status: Resolved

## Summary

Production had been silently broken since around July 5. Two independent issues stacked on top of each other, and both were invisible from the outside, the API kept returning HTTP 200 the whole time.

## Issue 1: Free Postgres database expired and was deleted

Render's free Postgres tier deletes databases 30 days after creation, plus a 14-day grace period, no backups, no recovery after that. The last confirmed Postgres work was mid-May. By late July the database was gone entirely, not visible anywhere in the Render project.

Every deploy since July 5 failed at startup with:

psycopg2.OperationalError: could not translate host name "dpg-..." to address: Name or service not known

Render auto-rolled back to the last successful deploy on each failure, which is why the site stayed up and looked fine, it was just running increasingly stale code.

All historical jobs, datasets, experiments, and any live probe_results rows are permanently lost. Nothing to restore, free tier keeps no backups.

Fix: provisioned a new Render Postgres instance (criterion-postgres, same Ohio region as the web service for private networking), updated DATABASE_URL in the web service's environment variables on Render.

## Issue 2: Production API keys had drifted from local .env

Separately, GEMINI_API_KEY and GROQ_API_KEY had been rotated locally after a leak (both keys were flagged by GitHub secret scanning and had to be replaced), but the old, revoked keys were still sitting in Render's environment variables. Local .env and Render's dashboard are two separate sources of truth, and rotating a secret in one doesn't touch the other.

This produced exactly the silent-downgrade failure named in the Phase 1 audit (gap 1.2): a live POST /jobs call with grader_name: llm_judge returned "grader": "llm_judge" with passed: true, but the reasoning field read "Fallback to contains_match after Gemini and Groq failed". The response looked completely normal unless you read the reasoning text.

Fix: updated GEMINI_API_KEY and GROQ_API_KEY in Render's environment to match the current local values.

## Verification

Live curl call with a correct prediction returned real judge reasoning: "The prediction perfectly matches the reference provided."

A second call with a wrong prediction (Berlin vs. reference Paris) correctly returned passed: false with reasoning explaining why, confirming the judge is discriminating, not rubber-stamping.

## Lesson

Environment variables in a deploy platform and a local .env file are two separate sources of truth. A secret rotation is only complete when both are updated, and there is currently no automated check that catches drift between them, the API returns a plausible-looking 200 response either way. Worth a smoke test in CI that asserts reasoning doesn't contain "Fallback" on a known-good judge call, closing this same gap for good instead of relying on catching it by hand next time.