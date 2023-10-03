# views.py
import aiohttp_jinja2
from aiohttp import web

from . import db

def redirect(router, route_name):
    location = router[route_name].url_for()
    return web.HTTPFound(location)

@aiohttp_jinja2.template('index.html')
async def index(request):
    year, pilots, flights, gliders = await db.get_main_counts()

    return {
            'year':year,
            'pilots': pilots,
            'flights': flights,
            'gliders': gliders
    }
@aiohttp_jinja2.template('pilots.html')
async def pilots(request):
    pilots = await db.get_pilots()
    #print(pilots)
    return  {'pilots':pilots}

async def load_pilots(request):
    if request.method == 'POST':
        # get next batch
        max_rank = await db.get_max_rank()
        #print(max_rank)
        # use xcontest loader 

        # save batch data to DB

        # redirect
        raise redirect(request.app.router, 'pilots')
    
    else:
        raise NotImplementedError("invalid?")