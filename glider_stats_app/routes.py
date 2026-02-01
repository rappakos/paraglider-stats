from fastapi import APIRouter
from .views import index, pilots, pilots_delta, gliders, glider


def setup_routes(app):
    # Create router with prefix from ROOT_PATH config
    router = APIRouter(prefix=app.state.config.ROOT_PATH)
    
    # GET routes
    router.add_api_route('/', index, methods=['GET'], name='index')
    router.add_api_route('/pilots', pilots, methods=['GET'], name='pilots')
    router.add_api_route('/pilots/delta', pilots_delta, methods=['GET'], name='pilots_delta')
    router.add_api_route('/gliders', gliders, methods=['GET'], name='gliders')
    router.add_api_route('/gliders/{glider}', glider, methods=['GET'], name='glider')
    
    # Include router in app
    app.include_router(router)