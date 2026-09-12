from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import get_config
from backend.app.routers import ai_router, auth_router, chat_router, note_router, oauth_router, user_router


def create_app():
    app_instance = FastAPI(title="MyNotableApp", version="1.0.0")
    config = get_config()
    app_instance.state.env = config
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
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