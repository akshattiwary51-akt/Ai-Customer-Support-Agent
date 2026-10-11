from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, auth, chat, health, knowledge, orchestration, orders, tickets
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.seed import seed_if_empty
from app.db.session import Base, engine


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup() -> None:
        if settings.auto_create_tables:
            Base.metadata.create_all(bind=engine)
            seed_if_empty()

    app.include_router(health.router)
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(chat.router, prefix=settings.api_prefix)
    app.include_router(orders.router, prefix=settings.api_prefix)
    app.include_router(tickets.router, prefix=settings.api_prefix)
    app.include_router(knowledge.router, prefix=settings.api_prefix)
    app.include_router(analytics.router, prefix=settings.api_prefix)
    app.include_router(orchestration.router, prefix=settings.api_prefix)
    return app


app = create_app()
