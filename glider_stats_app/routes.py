from .views import index, pilots, pilots_delta, gliders, glider


def setup_routes(app):
    # GET routes
    app.add_api_route('/', index, methods=['GET'], name='index')
    app.add_api_route('/pilots', pilots, methods=['GET'], name='pilots')
    app.add_api_route('/pilots/delta', pilots_delta, methods=['GET'], name='pilots_delta')
    app.add_api_route('/gliders', gliders, methods=['GET'], name='gliders')
    app.add_api_route('/gliders/{glider}', glider, methods=['GET'], name='glider')