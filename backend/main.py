import os
from fastapi import FastAPI
from backend.app.core.config import get_config
from backend.app.routers import ai_router, auth_router, chat_router, note_router, oauth_router, user_router


def create_app(env=None):
    selected_env = env or os.getenv("FASTAPI_ENV", "development")
    app_instance = FastAPI(title="MyNotableApp", version="1.0.0")
    app_instance.state.config = get_config()
    app_instance.state.env = selected_env

    # Routers
    app_instance.include_router(auth_router.router)
    app_instance.include_router(oauth_router.router)
    app_instance.include_router(user_router.router)
    app_instance.include_router(note_router.router)
    app_instance.include_router(ai_router.router)
    app_instance.include_router(chat_router.router)
    
    @app_instance.get("/health")
    def health():
        return {"status": "ok"}

    return app_instance


app = create_app()