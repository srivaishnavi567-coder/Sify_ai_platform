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

INVALID_NAMES = {
    "python",
    "python3",
    "ipython",
    "uvicorn",
    "gunicorn",
    "multiprocessing",
    "__main__",
}

def _clean(name: str | None) -> str | None:
    if not name:
        return None
    name = Path(name).stem
    return name if name not in INVALID_NAMES else None


def detect_app_name() -> str:
    """
    Determines app name from real app entrypoint or module path.
    Never uses working directory.
    """

    # 0️⃣ Explicit override (BEST PRACTICE)
    if os.getenv("SIFY_APP_NAME"):
        return os.getenv("SIFY_APP_NAME")

    # 1️⃣ python app.py
    try:
        name = _clean(sys.argv[0])
        if name:
            return name
    except Exception:
        pass

    # 2️⃣ python -m module OR uvicorn main:app
    try:
        import __main__
        main_file = getattr(__main__, "__file__", None)
        name = _clean(main_file)
        if name:
            return name
    except Exception:
        pass

    # 3️⃣ Inspect loaded modules (works for uvicorn/docker)
    try:
        for m in sys.modules.values():
            file = getattr(m, "__file__", None)
            if not file:
                continue

            p = Path(file)
            if "site-packages" in p.parts:
                continue
            if "uvicorn" in p.parts or "gunicorn" in p.parts:
                continue

            return p.stem
    except Exception:
        pass

    # 4️⃣ Honest fallback
    return "unknown_app"

