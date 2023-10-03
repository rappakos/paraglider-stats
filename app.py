import sys

import aiohttp_jinja2
import jinja2
from aiohttp import web


from glider_stats_app.routes import setup_routes
from glider_stats_app.middlewares import setup_middlewares
from glider_stats_app.db import setup_db
from glider_stats_app.driver import setup_web_driver

from config import DefaultConfig



CONFIG = DefaultConfig()



async def init_app(argv=None):

    app = web.Application()

    #app['config'] = get_config(argv)

    # setup Jinja2 template renderer
    aiohttp_jinja2.setup(
        app, loader=jinja2.PackageLoader('glider_stats_app', 'templates'))

    # setup db
    await setup_db(app)

    setup_web_driver(app)    

    # setup views and routes
    setup_routes(app)

    setup_middlewares(app)

    return app


def main(argv):

    app = init_app(argv)

    web.run_app(app,
                host='localhost',
                port=CONFIG.PORT)


if __name__ == '__main__':
    main(sys.argv[1:])