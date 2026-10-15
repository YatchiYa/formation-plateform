import os

import uvicorn
from google.adk.cli.fast_api import get_fast_api_app

# ADK builds the whole HTTP API for us (/list-apps, /apps/.../sessions, /run, /run_sse).
# Every sub-folder of agents/ that exposes `root_agent` becomes one "app".
app = get_fast_api_app(
    agents_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents"),
    # None = in-memory sessions (lost on restart). See README "Sessions" for durable options.
    session_service_uri=os.getenv("SESSION_SERVICE_URI"),
    web=os.getenv("SERVE_WEB_UI", "false") == "true",
    # Sends traces/logs/metrics to Cloud Trace / Logging / Monitoring.
    otel_to_cloud=os.getenv("OTEL_TO_CLOUD", "false") == "true",
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
