# import os
# import sys
# from pathlib import Path

# def detect_app_name() -> str:
#     if os.getenv("SIFY_APP_NAME"):
#         return os.getenv("SIFY_APP_NAME")

#     if os.getenv("OTEL_SERVICE_NAME"):
#         return os.getenv("OTEL_SERVICE_NAME")

#     try:
#         entry = Path(sys.argv[0]).stem
#         if entry and entry not in {"python", "ipython"}:
#             return entry
#     except Exception:
#         pass

#     try:
#         cwd_name = Path.cwd().name
#         if cwd_name:
#             return cwd_name
#     except Exception:
#         pass
# import os
# import sys
# from pathlib import Path

# INVALID_NAMES = {
#     "python",
#     "python3",
#     "ipython",
#     "uvicorn",
#     "gunicorn",
#     "multiprocessing",
#     "__main__",
# }

# def detect_app_name() -> str:
#     """
#     Best-effort app name detection.
#     Tries filename / module path / cwd.
#     Falls back to 'unknown_app' if not determinable.
#     """

#     # 1️⃣ Try entry script (python app.py)
#     try:
#         if sys.argv and sys.argv[0]:
#             entry = Path(sys.argv[0]).stem
#             if entry and entry not in INVALID_NAMES:
#                 return entry
#     except Exception:
#         pass

#     # 2️⃣ Try __main__.__file__ (python -m package)
#     try:
#         import __main__
#         main_file = getattr(__main__, "__file__", None)
#         if main_file:
#             name = Path(main_file).stem
#             if name and name not in INVALID_NAMES:
#                 return name
#     except Exception:
#         pass

#     # 3️⃣ Try current working directory name
#     try:
#         cwd_name = Path.cwd().name
#         if cwd_name and cwd_name not in INVALID_NAMES:
#             return cwd_name
#     except Exception:
#         pass

#     # 4️⃣ Absolute fallback
#     return "unknown_app"
import os
import sys
from pathlib import Path

INVALID = {
    "uvicorn",
    "gunicorn",
    "python",
    "__main__",
}

def detect_app_name() -> str:
    # 0️⃣ Explicit config always wins
    if os.getenv("SIFY_APP_NAME"):
        return os.getenv("SIFY_APP_NAME")

    # 1️⃣ uvicorn module:app (Windows-safe)
    for arg in sys.argv:
        # must look like module:attr (not a path like C:\...)
        if ":" in arg and "\\" not in arg and "/" not in arg:
            module = arg.split(":", 1)[0]
            name = module.split(".")[-1]
            if name and name not in INVALID:
                return name

    # 2️⃣ python file.py
    try:
        entry = Path(sys.argv[0]).stem
        if entry and entry not in INVALID:
            return entry
    except Exception:
        pass

    # 3️⃣ Honest fallback
    return "unknown_app"



