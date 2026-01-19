import os
import sys
from pathlib import Path

def _detect_app_name() -> str:
    # 1️⃣ Explicit SDK override
    if os.getenv("SIFY_APP_NAME"):
        return os.getenv("SIFY_APP_NAME")

    # 2️⃣ OpenTelemetry standard
    if os.getenv("OTEL_SERVICE_NAME"):
        return os.getenv("OTEL_SERVICE_NAME")

    # 3️⃣ Entrypoint script name (BEST DEFAULT)
    try:
        entry = Path(sys.argv[0]).stem
        if entry and entry not in {"python", "ipython"}:
            return entry
    except Exception:
        pass

    # 4️⃣ Project / working directory name
    try:
        cwd_name = Path.cwd().name
        if cwd_name:
            return cwd_name
    except Exception:
        pass

    # Absolute last-resort (but meaningful)
    return "sify-client-app"
