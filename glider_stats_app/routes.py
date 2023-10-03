import pathlib

from .views import index,pilots,load_pilots

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/pilots', pilots, name='pilots') # show current
    app.router.add_post('/pilots', load_pilots, name='load_pilots') # download a new batch