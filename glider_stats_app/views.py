# views.py
import os
import aiohttp_jinja2
from aiohttp import web

from . import db
from . import xcontest_loader

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
    return  {'pilots':pilots,
            'allow_delete': request.app.config.ALLOW_DELETE }

async def load_pilots(request):
    if request.method == 'POST':
        # get next batch
        max_rank = await db.get_max_rank()
        # parse xcontest
        driver=request.app.driver
        pilots = await xcontest_loader.load_pilots(driver, max_rank)
        await db.save_pilots(pilots)
        # redirect
        raise redirect(request.app.router, 'pilots')
    else:
        raise NotImplementedError("invalid?")
    
async def delete_pilots(request):
    if request.method == 'POST':
        await db.delete_pilots()

    raise redirect(request.app.router, 'pilots')

@aiohttp_jinja2.template('gliders.html')
async def gliders(request):
    unclass_gliders = await db.get_unclassed_gliders()
    gliders = await db.get_gliders()

    return {
            'unclass_gliders':unclass_gliders,
            'gliders':gliders
        }