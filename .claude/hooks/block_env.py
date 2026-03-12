import json
import sys

try:
    data = json.load(sys.stdin)
    path = data.get("file_path", "")
    filename = path.replace("\\", "/").split("/")[-1]

    if filename == ".env" or (filename.startswith(".env.") and filename != ".env.example"):
        print(json.dumps({"decision": "block", "reason": f"Access to '{filename}' is not allowed."}))
        sys.exit(2)
except Exception:
    pass

sys.exit(0)
