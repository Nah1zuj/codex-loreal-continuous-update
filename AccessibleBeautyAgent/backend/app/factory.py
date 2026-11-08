"""HTTP factory; importing it creates no default application or database."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings, local_origins
from app.agent.coaching import CommandConflict
from app.privacy import BrowserIdentityMiddleware
from app.composition import build_services
from app.extensions import ExtensionSpec, validate_extensions
from app.routes.api import build_router
from app.routes.recollection import build_recollection_router
from app.routes.makeup import build_makeup_router
from app.routes.conversation import build_conversation_router
from app.routes.local_vision import build_local_vision_router
from app.routes.journal import build_journal_router, build_transcript_records_router
from app.routes.full_look import build_full_look_router
from app.routes.reading import build_reading_router
from app.routes.admin import build_admin_router


def create_app(settings: Settings | None = None, *, extensions: tuple[ExtensionSpec, ...] = ()):
    extensions = validate_extensions(extensions)
    services = build_services(settings if settings is not None else Settings())
    settings, agent, memory = services.settings, services.agent, services.agent.memory
    app = FastAPI(title='Accessible Beauty Agent', version='0.1.0')
    app.state.services = services
    app.state.agent = agent
    app.state.conversation = services.conversation
    app.state.settings = settings
    app.state.knowledge_admin = services.knowledge_admin
    app.add_middleware(CORSMiddleware,allow_origins=local_origins(),allow_methods=['GET','POST','DELETE'],allow_headers=['Content-Type'])
    app.add_middleware(BrowserIdentityMiddleware,agent=agent,settings=settings)
    @app.get('/api/identity')
    def identity():return {'mode':'private_browser','account_login':False,'retention_days':30}
    @app.exception_handler(KeyError)
    async def missing(request: Request, exc: KeyError):
        return JSONResponse(status_code=404,content={'detail':str(exc.args[0])})
    @app.exception_handler(PermissionError)
    async def forbidden(request: Request, exc: PermissionError):
        return JSONResponse(status_code=403,content={'detail':str(exc)})
    @app.exception_handler(CommandConflict)
    async def command_conflict(request: Request, exc: CommandConflict):
        return JSONResponse(status_code=409,content={'code':exc.code,'detail':str(exc)})
    @app.exception_handler(ValueError)
    async def invalid(request: Request, exc: ValueError):
        # Reject invalid provider output without trusting it as observation.
        return JSONResponse(status_code=409,content={'detail':str(exc)})
    @app.exception_handler(RuntimeError)
    async def provider_error(request: Request, exc: RuntimeError):
        return JSONResponse(status_code=503,content={'detail':str(exc)})
    app.include_router(build_router(agent,settings,app.state.conversation))
    app.include_router(build_recollection_router(agent))
    app.include_router(build_makeup_router(agent))
    app.include_router(build_conversation_router(app.state.conversation))
    app.include_router(build_local_vision_router(agent))
    app.include_router(build_journal_router(memory,agent,app.state.conversation))
    app.include_router(build_transcript_records_router(memory))
    app.include_router(build_full_look_router(agent))
    app.include_router(build_reading_router(settings))
    app.include_router(build_admin_router(app.state.knowledge_admin,settings))
    try:
        from app.routes.hardware import build_hardware_router
    except ModuleNotFoundError as exc:
        if exc.name!='trace_hardware':raise
        @app.get('/api/hardware/devices')
        def hardware_unavailable():return {'devices':[],'available':False,'detail':'Install the optional local hardware package'}
    else:
        app.include_router(build_hardware_router(agent))
    for extension in extensions:
        app.include_router(extension.build_router(services), prefix=f'/api/extensions/{extension.name}')
    return app
