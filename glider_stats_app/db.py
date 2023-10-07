# db.py
import aiosqlite
from sqlalchemy import create_engine,text

DB_NAME = './glider_stats.db'
INIT_SCRIPT = './glider_stats_app/init_db.sql'

async def setup_db(app):
    app['DB_NAME'] = DB_NAME
    async with aiosqlite.connect(DB_NAME) as db:
        # only test
        async with db.execute("SELECT 'db check'") as cursor:
            async for row in cursor:
                print(row[0])

        #
        with open(INIT_SCRIPT, 'r') as sql_file:
            sql_script = sql_file.read()
            await db.executescript(sql_script)
            await db.commit()


async def get_main_counts():
    year, pilots, flights, gliders = 2023,0,0,0
    async with aiosqlite.connect(DB_NAME) as db:
        param = {'year':year}
        async with db.execute("""SELECT [year], count(pilot_id) [pilots]
                                 FROM pilots 
                                 WHERE year = :year 
                                 GROUP BY [year]""",param) as cursor:
            async for row in cursor:
                year = row[0]
                pilots = row[1]
        async with db.execute("""SELECT count(f.flight_id) [flights]
                                 FROM pilots p
                                 INNER JOIN flights f ON f.pilot_id=p.pilot_id
                                 WHERE p.year = :year 
                                 GROUP BY [year]""",param) as cursor:
            async for row in cursor:
                flights = row[0]

        async with db.execute("""SELECT count(distinct f.glider) [gliders]
                                 FROM pilots p
                                 INNER JOIN flights f ON f.pilot_id=p.pilot_id
                                 WHERE p.year = :year 
                                 GROUP BY [year]""",param) as cursor:
            async for row in cursor:
                gliders = row[0]


    return  year, pilots, flights, gliders  

async def get_unclassed_gliders():
        year = 2023
        gliders = []
        async with aiosqlite.connect(DB_NAME) as db:
            param = {'year':year}
            async with db.execute("""SELECT f.glider, count(*) [count]
                    FROM flights f 
                    WHERE NOT EXISTS (SELECT 1 FROM gliders g WHERE g.glider=f.glider COLLATE NOCASE)
                        AND f.glider <> ''
                    GROUP BY f.glider  
                    HAVING count(*) > 10
                    ORDER BY count(*) DESC
                    LIMIT 5 """,param) as cursor:
                async for row in cursor:
                    gliders.append({
                        'glider': row[0],
                        'flight_count':  row[1]
                    })
        return gliders


def lognormal_1( mu, sigma):
    import math
    return 0.5*(1.0 + math.erf(mu/sigma/math.sqrt(2.0)))

async def get_gliders():
        import math
        import pandas as pd
        import numpy as np

        year, point_goal, min_count = 2023, 100.0, 50

        engine = create_engine(f'sqlite:///{DB_NAME}')
        with engine.connect() as db:
            param = {'year':year}
            df  = pd.read_sql_query(text("""
                        SELECT 
                                    g.glider_norm
                                    , g.class
                                    , cast(f.flight_points as float) [xc]
                        FROM flights f 
                        INNER JOIN gliders g ON g.glider=f.glider COLLATE NOCASE                       
                    """), db, params=param)
            
        df = df.groupby(['glider_norm','class'])['xc'].agg([
            ('count', len),
            ('mu', lambda value: np.mean(np.log(value/point_goal)) ),
            ('sigma', lambda value: np.std(np.log(value/point_goal)) )
        ])

        df['p50'] = df.apply(lambda row: lognormal_1(row.mu-math.log(0.5),row.sigma), axis=1)
        df['p100'] = df.apply(lambda row: lognormal_1(row.mu,row.sigma), axis=1)
        df['p200'] = df.apply(lambda row: lognormal_1(row.mu-math.log(2.0),row.sigma), axis=1)
        #print(df.columns)
        df = df[df['count'] > min_count ].sort_values(by=['p100'], ascending=False)
        print(df.head(10))

        return df.reset_index().to_dict('records')

async def get_glider(glider:str):
    import math
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    from base64 import b64encode

    year,point_goal = 2023, 100
    async with aiosqlite.connect(DB_NAME) as db:
        param = {'year':year,'glider_safe':glider.replace("-"," ")}
        glider_norm, g_class, g_count, p_count, points = None, None, 0,0,[]
        async with db.execute("""SELECT g.glider_norm, g.class
                            , count(*) [count]
                            , count(distinct p.pilot_id) [pilot_count]
                    FROM pilots p
                    INNER JOIN flights f ON f.pilot_id=p.pilot_id
                    INNER JOIN gliders g ON g.glider=f.glider COLLATE NOCASE       
                    WHERE p.[year]= :year
                        and g.glider_norm = :glider_safe COLLATE NOCASE  
                    GROUP BY  g.glider_norm """,param) as cursor:
            async for row in cursor:
                glider_norm=row[0]
                g_class = row[1]
                g_count = row[2]
                p_count= row[3]
        if glider_norm:
            async with db.execute("""SELECT cast(f.flight_points as float) [xc]
                    FROM pilots p
                    INNER JOIN flights f ON f.pilot_id=p.pilot_id
                    INNER JOIN gliders g ON g.glider=f.glider COLLATE NOCASE       
                    WHERE p.[year]= :year
                        and g.glider_norm = :glider_safe COLLATE NOCASE 
                    ORDER BY cast(f.flight_points as float) ASC """,param) as cursor:
             async for row in cursor:
                 points.append(row[0])

        #print(points)
        logp = [math.log(p/point_goal) for p in points]
        mu, sigma = np.mean(logp), np.std(logp)

        # plot - TODO check if dash module is simpler
        fig = px.scatter( x=points, y=np.arange(len(points)))
        xrange = np.arange(1,500)
        fig.add_trace(go.Scatter(x=xrange, \
                                y= [len(points)*0.5*(1.0+math.erf((math.log(x/point_goal) - mu)/sigma/math.sqrt(2.0) )) for x in xrange], \
                                mode='lines', showlegend=False ))

        fig.update_xaxes(title='xc points',range=[0,500])
        fig.update_yaxes(title='flight number',  range=[0, math.floor((len(points) / 100)+1)*100 ])
        img_bytes = fig.to_image(format="png")

        encoding = b64encode(img_bytes).decode()
        img_b64 = "data:image/png;base64," + encoding


    return {
        'glider_norm': glider_norm,
        'class': g_class,
        'count': g_count,
        'pilot_count': p_count,
        'mu': mu,
        'sigma': sigma,
        'img_b64': img_b64
    }

async def get_pilots():
    year = 2023 # TODO pass as param?
    res = []
    async with aiosqlite.connect(DB_NAME) as db:
        param = {'year': year,"page_size": 20}
        async with db.execute("""SELECT xc_rank, pilot_id, username
                                 FROM pilots 
                                 WHERE year = :year 
                                 ORDER BY xc_rank DESC
                                 LIMIT :page_size """,param) as cursor:
            async for row in cursor:
                 res.append({
                        'rank':row[0],
                        'pilot_id':row[1],
                        'username':row[2]
                        })
    return res

async def get_max_rank():
    year = 2023 # TODO pass as param?
    async with aiosqlite.connect(DB_NAME) as db:
        param = {'year': year}
        async with db.execute("""SELECT MAX(xc_rank) 
                                 FROM pilots
                                 WHERE year = :year """,param) as cursor:
            async for row in cursor:
                return row[0] or 0

async def delete_pilots():
     async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""DELETE FROM pilots """)        
        await db.commit()

async def save_pilots(pilots):
    year = 2023 # TODO pass as param?
    async with aiosqlite.connect(DB_NAME) as db:
        for pilot in pilots:
            params = {
                'year': year,
                'xc_rank':  pilot['xc_rank'],
                'username': pilot['username'],
                'pilot_id': pilot['pilot_id']
            }
            #print(params)
            res = await db.execute_insert("""
                    INSERT INTO pilots ([year],[xc_rank], username, pilot_id)
                    SELECT :year, :xc_rank, :username, :pilot_id
                    WHERE NOT EXISTS (SELECT 1 FROM pilots p WHERE p.[year]=:year AND p.[pilot_id]=:pilot_id )
                """, params)
            #print(res)
            if pilot['flights']:
                for flight in pilot['flights']:
                    params = {
                        'pilot_id': pilot['pilot_id'],
                        'flight_id': flight['flight_id'],
                        'launch': flight['launch'],
                        'flight_type': flight['flight_type'],
                        'flight_length': flight['flight_length'],
                        'flight_points': flight['flight_points'],
                        'glider': flight['glider'],
                        'details': flight['details']
                    }
                    await db.execute("""
                        INSERT INTO flights
                                (pilot_id, flight_id, launch,flight_type,flight_length,flight_points, glider, details)
                        SELECT :pilot_id, :flight_id, :launch,:flight_type,:flight_length,:flight_points, :glider, :details
                        WHERE NOT EXISTS (SELECT 1 FROM flights f WHERE f.flight_id = :flight_id)
                        """, params)

        await db.commit()