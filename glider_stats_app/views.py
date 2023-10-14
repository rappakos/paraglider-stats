# views.py
import os
import aiohttp_jinja2
from aiohttp import web,streamer

from . import db
from . import xcontest_loader

def redirect(router, route_name):
    location = router[route_name].url_for()
    return web.HTTPFound(location)

@aiohttp_jinja2.template('index.html')
async def index(request):
    year, pilots, flights, gliders = await db.get_main_counts()

    e_pilots, e_flights, e_gliders = await db.get_eval_counts()

    df =  await db.get_pilots_by_manufacturer()
    stats_by_manufacturer = df.reset_index().to_dict('records')

    #print(stats_by_manufacturer)

    return {
            'year':year,
            'total': {
                'pilots': pilots,
                'flights': flights,
                'gliders': gliders
            },
            'evaluated': {
                'pilots': e_pilots,
                'flights': e_flights,
                'gliders': e_gliders
            },
            'manufacturers': stats_by_manufacturer
    }

@aiohttp_jinja2.template('pilots.html')
async def pilots(request):
    pilots = await db.get_pilots()
    #print(pilots)
    return  {'pilots':pilots,
            'allow_delete': request.app.config.ALLOW_DELETE }

async def load_pilots(request):
    if not request.app.config.START_DRIVER:
        raise redirect(request.app.router, 'pilots')

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


@streamer
async def file_sender(writer, xlsx_data=None):
    import io
    #print(type(xlsx_data))
    with io.BytesIO(xlsx_data) as f:
        chunk = f.read(2 ** 16)
        while chunk:
            await writer.write(chunk)
            chunk = f.read(2 ** 16)


@aiohttp_jinja2.template('gliders.html')
async def gliders(request):
    import io
    import pandas as pd
    from datetime import datetime

    glider, g_class, unclass, compare = request.rel_url.query.get('glider',''), \
                               request.rel_url.query.get('class',''), \
                               request.rel_url.query.get('unclass',''), \
                               [g for g in request.rel_url.query.keys() if g not in ['glider','class','export','unclass']]
    #print(compare)



    
    comparison = await db.get_comparison(compare) if compare else None

    if 'export' in request.rel_url.query.keys():
        # other data
        df = await db.get_gliders(glider='', g_class='')
        df.drop(columns=['count2'], inplace=True)
        df = df.rename(columns={"glider_norm": "glider name", "count": "flight count"})
        year, pilots, flights, gliders = await db.get_main_counts()
        e_pilots, e_flights, e_gliders = await db.get_eval_counts() 
        df_totals = pd.DataFrame([
            ['total',pilots, flights, gliders],
            ['evaluated',e_pilots, e_flights, e_gliders]
        ], columns=['counts','pilots','flights','glider name'])
        df_manu = await db.get_pilots_by_manufacturer()
        df_unclass = pd.DataFrame(await db.get_unclassed_gliders(glider='', top=1000))

        headers = {
            "Content-disposition": f'attachment; filename=xcontest.2023.sport.{datetime.now().strftime("%Y%d%m.%H%M%S")}.xlsx'
        }
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_totals.to_excel(writer, sheet_name='overview',index=False)
            df_manu.to_excel(writer, sheet_name='manufacturers',index=True)
            df.to_excel(writer, sheet_name='gliders',index=True)
            df_unclass.to_excel(writer, sheet_name='unevaluated',index=False)
       
        return web.Response(
                body=file_sender(xlsx_data=output.getvalue()),
                headers=headers
            )

    else:
        unclass_gliders = await db.get_unclassed_gliders(unclass)
        df = await db.get_gliders(glider=glider, g_class=g_class)
        gliders = df.reset_index().to_dict('records')

        return {
            'unclass_gliders':unclass_gliders,
            'gliders':gliders,
            'comparison': comparison,
            'filter': {
                'glider':glider,
                'class':g_class,
                'compare': compare,
                'unclass': unclass
            }
        }

@aiohttp_jinja2.template('glider.html')
async def glider(request):
    glider = request.match_info['glider']

    data = await db.get_glider(glider)

    return data