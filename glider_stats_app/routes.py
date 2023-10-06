import pathlib

from .views import index,pilots,load_pilots,delete_pilots,gliders,glider

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/pilots', pilots, name='pilots') # show current
    app.router.add_post('/pilots', load_pilots, name='load_pilots') # download a new batch
    app.router.add_post('/pilots/delete', delete_pilots, name='delete_pilots')

    app.router.add_get('/gliders', gliders, name='gliders')
    app.router.add_get('/gliders/{glider}', glider, name='glider')