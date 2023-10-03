import pathlib

from .views import index,pilots,load_pilots

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/pilots', pilots)
    # app.router.add_post('/pilots/load', load_pilots)