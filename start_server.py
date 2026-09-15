#!/usr/bin/env python3

import uvicorn

from app.core.config import Settings

settings = Settings()

if __name__ == "__main__":
    if settings.test_mode:
        print(f"Starting server | test_mode: {settings.test_mode}")

    uvicorn.run(
        app="app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_excludes=[
            "app/tests/conftest.py",
            "app/tests/test_root.py",
            "app/tests/test_users_router.py",
            "app/tests/test_books_router.py",
        ],
    )
