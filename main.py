"""
智居物语 — 主入口
"""
import os
import logging
import uvicorn

import config

# ── Logging ──
os.makedirs(config.LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(config.LOGS_DIR / "system.log"), encoding="utf-8"),
    ]
)

if __name__ == "__main__":
    uvicorn.run(
        "web.app:app",
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        reload=True,
    )
