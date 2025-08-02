# Backup of original main.py - replaced by main_simplified.py
# from app import app  # noqa: F401

# if __name__ == "__main__":
#     import os
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port, debug=False)

# NEW SIMPLIFIED VERSION
from app_simplified import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
