# views.py
import os
import io
from typing import Optional
import pandas as pd
from datetime import datetime

from fastapi import Request, Query
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

from . import db


async def index(request: Request, y: Optional[str] = Query(None)):
    year = y if y else os.environ.get('YEAR')
    
    year, pilots, flights, gliders = await db.get_main_counts(year)

    e_pilots, e_flights, e_gliders = await db.get_eval_counts(year)

    df = await db.get_pilots_by_manufacturer(year)
    
    if year in [2025, 2024]:
        df_prev = await db.get_pilots_by_manufacturer(year-1)
        df = pd.merge(df, df_prev, how="left", on=["manufacturer"], suffixes=('', '_prev'))
    else: 
        # hack...
        df = pd.merge(df, df, how="left", on=["manufacturer"], suffixes=('', '_prev'))

    stats_by_manufacturer = df.reset_index().to_dict('records')

    context = {
        'request': request,
        'year': year,
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
    
    return request.app.state.templates.TemplateResponse('index.html', context)


async def pilots(request: Request):
    pilots_list = await db.get_pilots()
    
    context = {
        'request': request,
        'pilots': pilots_list,
        'allow_delete': request.app.state.config.ALLOW_DELETE
    }
    
    return request.app.state.templates.TemplateResponse('pilots.html', context)


def classify(row):
    return f"{row[('class_prev', 'max')]}{row[('class', 'min')]}"


async def pilots_delta(request: Request):
    df1 = await db.get_pilot_gliders(2025)
    df2 = await db.get_pilot_gliders(2024)
    df = pd.merge(df1, df2, how='left', on=['pilot_id'], suffixes=('', '_prev'))
    
    dfagg = df.groupby(['pilot_id'])[['class', 'class_prev']].agg({'class': ['min'], 'class_prev': ['max']})
    print(dfagg.columns.values)
    dfagg['delta'] = dfagg.apply(classify, axis=1)
    dfagg = dfagg.groupby('delta').count().reset_index()
    
    dfagg.columns = ['delta', 'count', 'count2']
    res = dfagg.to_dict('records')
    print(res)

    context = {
        'request': request,
        'pilots': res,
        'allow_delete': False
    }
    
    return request.app.state.templates.TemplateResponse('pilots_delta.html', context)


async def gliders(
    request: Request,
    y: Optional[str] = Query(None),
    glider: Optional[str] = Query(''),
    g_class: Optional[str] = Query('', alias='class'),
    unclass: Optional[str] = Query(''),
    export: Optional[str] = Query(None)
):
    year = y if y else os.environ.get('YEAR')

    # Get comparison gliders from query params
    compare = [key for key in request.query_params.keys() 
               if key not in ['y', 'glider', 'class', 'export', 'unclass']]
    
    comparison = await db.get_comparison(year, compare) if compare else None

    if export is not None:
        # Excel export
        df = await db.get_gliders(glider='', g_class='')
        df.drop(columns=['count2'], inplace=True)
        df = df.rename(columns={"glider_norm": "glider name", "count": "flight count"})
        
        year_val, pilots, flights, gliders_count = await db.get_main_counts()
        e_pilots, e_flights, e_gliders = await db.get_eval_counts() 
        
        df_totals = pd.DataFrame([
            ['total', pilots, flights, gliders_count],
            ['evaluated', e_pilots, e_flights, e_gliders]
        ], columns=['counts', 'pilots', 'flights', 'glider name'])
        
        df_manu = await db.get_pilots_by_manufacturer()
        df_unclass = pd.DataFrame(await db.get_unclassed_gliders(glider='', top=1000))

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_totals.to_excel(writer, sheet_name='overview', index=False)
            df_manu.to_excel(writer, sheet_name='manufacturers', index=True)
            df.to_excel(writer, sheet_name='gliders', index=True)
            df_unclass.to_excel(writer, sheet_name='unevaluated', index=False)
        
        output.seek(0)
        
        filename = f'xcontest.{year}.sport.{datetime.now().strftime("%Y%d%m.%H%M%S")}.xlsx'
        headers = {
            "Content-Disposition": f'attachment; filename={filename}'
        }
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
    else:
        unclass_gliders = await db.get_unclassed_gliders(unclass)
        df = await db.get_gliders(glider=glider, g_class=g_class, year=year)
        gliders_list = df.reset_index().to_dict('records')

        context = {
            'request': request,
            'year': year,
            'unclass_gliders': unclass_gliders,
            'gliders': gliders_list,
            'comparison': comparison,
            'filter': {
                'glider': glider,
                'class': g_class,
                'compare': compare,
                'unclass': unclass
            }
        }
        
        return request.app.state.templates.TemplateResponse('gliders.html', context)


async def glider(request: Request, glider: str):
    data = await db.get_glider(glider)
    data['request'] = request
    
    return request.app.state.templates.TemplateResponse('glider.html', data)