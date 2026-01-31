# middlewares.py
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import logging

logger = logging.getLogger(__name__)


async def handle_404(request: Request, exc: HTTPException):
    context = {'request': request}
    return request.app.state.templates.TemplateResponse('404.html', context, status_code=404)


async def handle_500(request: Request, exc: Exception):
    context = {'request': request}
    return request.app.state.templates.TemplateResponse('500.html', context, status_code=500)


def setup_middlewares(app):
    @app.exception_handler(404)
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if exc.status_code == 404:
            return await handle_404(request, exc)
        raise exc
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception("Error handling request")
        return await handle_500(request, exc)