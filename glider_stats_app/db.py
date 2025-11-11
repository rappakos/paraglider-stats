# db.py
import aiosqlite
from sqlalchemy import create_engine,text

DB_NAME = './glider_stats.db'
INIT_SCRIPT = './glider_stats_app/init_db.sql'
DB_NAME_F = './glider_stats_{year}.db'


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


async def get_main_counts(year:int):
    pilots, flights, gliders = 0,0,0
    async with aiosqlite.connect(DB_NAME_F.format(year=year)) as db:
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

async def get_eval_counts(year:int):
    pilots, flights, gliders = 0,0,0
    async with aiosqlite.connect(DB_NAME_F.format(year=year)) as db:
        param = {'year':year}
        async with db.execute("""SELECT count(distinct p.pilot_id) [pilots]
                                        ,count(distinct f.flight_id) [flights]
                                        ,count(distinct f.glider) [gliders]
                                 FROM pilots p
                                 INNER JOIN flights f ON f.pilot_id=p.pilot_id
                                 INNER JOIN gliders g ON g.glider=f.glider COLLATE NOCASE
                                 WHERE p.year = :year 
                                 GROUP BY [year]""",param) as cursor:
            async for row in cursor:
                pilots = row[0]
                flights = row[1]
                gliders = row[2]

    return  pilots, flights, gliders  

async def get_pilots_by_manufacturer(year:int):
        import pandas as pd

        dbName= DB_NAME_F.format(year=year)
        engine = create_engine(f'sqlite:///{dbName}')
        with engine.connect() as db:
            param = {'year':year}
            #print(param)
            df  = pd.read_sql_query(text(f"""
                        SELECT  g.glider_norm
                                    , g.class
                                    , count( distinct f.pilot_id) [pilots]
                        FROM flights f 
                        INNER JOIN gliders g ON g.glider=f.glider COLLATE NOCASE
                        GROUP BY g.glider_norm COLLATE NOCASE, g.class
                        ORDER BY count( distinct f.pilot_id) DESC
                    """), db, params=param)
        
        df['manufacturer'] = df.apply(lambda row: row.glider_norm.split(' ')[0], axis=1)
        
        df = df.groupby(['manufacturer','class'])['pilots'].agg([('pilots', sum)]).reset_index()
        #print(df.head())
        df = pd.pivot_table(df,index='manufacturer', columns='class', values='pilots', fill_value=0)
        df['pilots'] = df.apply(lambda row: row.A + row.B + row.C, axis=1)
        #df['pilots'] = df.apply(lambda row: row.B + row.C, axis=1)
        #print(df.head())

        return df.sort_values(by='pilots',ascending=False)
        

async def get_unclassed_gliders(glider:str,top:int=20):
        year = 2025
        gliders = []
        #print(glider)
        async with aiosqlite.connect(DB_NAME) as db:
            param = {'year':year}
            async with db.execute(f"""SELECT f.glider, count(*) [count]
                    FROM flights f 
                    WHERE NOT EXISTS (SELECT 1 FROM gliders g WHERE g.glider=f.glider COLLATE NOCASE)
                        AND f.glider <> ''
                        AND LOWER(f.glider) like '%{glider.lower()}%'
                    GROUP BY f.glider  
                    --HAVING count(*) >= 10
                    ORDER BY count(*) DESC
                    LIMIT {top} """,param) as cursor:
                async for row in cursor:
                    gliders.append({
                        'glider': row[0],
                        'flight_count':  row[1]
                    })
        return gliders


def lognormal_1( mu, sigma):
    import math
    return 0.5*(1.0 + math.erf(mu/sigma/math.sqrt(2.0)))

async def get_gliders(glider:str, g_class:str, year:int):
        import math
        import pandas as pd
        import numpy as np

        point_goal, min_count = 100.0, 50

        dbName= DB_NAME_F.format(year=year)
        engine = create_engine(f'sqlite:///{dbName}')
        with engine.connect() as db:
            param = {'year':year}
            #print(param)
            df  = pd.read_sql_query(text(f"""
                        SELECT 
                                    g.glider_norm
                                    , g.class
                                    , cast(f.flight_points as float) [xc]
                        FROM flights f 
                        INNER JOIN gliders g ON g.glider=f.glider COLLATE NOCASE
                        WHERE (LOWER(g.glider_norm) like '%{glider.lower()}%' AND LOWER(g.class) like '%{g_class.lower()}%')
                    """), db, params=param)
        #print(df.head())    
        
        df = df.groupby(['glider_norm','class'])['xc'].agg([
            ('count', len),
            ('count2', len),
            ('mu', lambda value: np.mean(np.log(value/point_goal)) ),
            ('sigma', lambda value: np.std(np.log(value/point_goal)) )
        ])

        if not df.empty:
            df['confidence'] =  df.apply(lambda row: 1.96*math.sqrt(row.sigma**2/float(row.count2) + 0.5*row.sigma**4/(row.count2-1.0)) ,axis=1)
            df['p50'] = df.apply(lambda row: lognormal_1(row.mu-math.log(0.5),row.sigma), axis=1)
            df['p100'] = df.apply(lambda row: lognormal_1(row.mu,row.sigma), axis=1)
            df['p200'] = df.apply(lambda row: lognormal_1(row.mu-math.log(2.0),row.sigma), axis=1)
            
            #print(df.columns)
            df = df[df['count'] > min_count ].sort_values(by=['p100'], ascending=False)
        else:
            print('empty')

        #print(df.head(10))

        return df

def map_fig_to_b64(fig):
    from base64 import b64encode

    img_bytes = fig.to_image(format="png")
    encoding = b64encode(img_bytes).decode()
    return "data:image/png;base64," + encoding

async def get_glider(glider:str):
    import math
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    from scipy import special

    year,point_goal = 2025, 100
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

        flights = []       
        if glider_norm:
            async with db.execute("""SELECT cast(f.flight_points as float) [xc]
                        , f.pilot_id
                        , f.launch
                        , f.flight_type
                    FROM pilots p
                    INNER JOIN flights f ON f.pilot_id=p.pilot_id
                    INNER JOIN gliders g ON g.glider=f.glider COLLATE NOCASE       
                    WHERE p.[year]= :year
                        and g.glider_norm = :glider_safe COLLATE NOCASE 
                    ORDER BY cast(f.flight_points as float) ASC """,param) as cursor:
             async for row in cursor:
                points.append(row[0])
                flights.insert(0, {
                    "xc_points" : row[0],
                    "pilot_id": row[1],
                    "launch": row[2],
                    "flight_type": row[3]
                })


        #print(points)
        logp = [math.log(p/point_goal) for p in points]
        mu, sigma, confidence = np.mean(logp), np.std(logp), 1.96*np.std(logp)/math.sqrt(len(points))
        # lognormal - method of moments
        Ex, Vx = np.mean(points)/point_goal, np.var(points)/point_goal**2        
        mu2, sigma2 = math.log(Ex/math.sqrt(1.0 + Vx/Ex**2)), math.sqrt(math.log(1.0 + Vx/Ex**2))
        # Gamma dist - method of moments
        gamma_k, gamma_theta = Ex**2/Vx, Vx/Ex

        print(f"""
            naive mu = {mu}, sigma = {sigma}
            m-o-m mu = {mu2}, sigma = {sigma2}
            m-o-m k = {gamma_k}, theta = {gamma_theta}
            """)


        # plot - TODO check if dash module is simpler
        fig = px.scatter( x=np.arange(len(points)), y=points)
        xrange = np.arange(1,500)
        fig.add_trace(go.Scatter(x= [len(points)*0.5*(1.0+math.erf((math.log(x/point_goal) - mu)/sigma/math.sqrt(2.0) )) for x in xrange], \
                                y=xrange, \
                                mode='lines', showlegend=False ))
        fig.add_trace(go.Scatter(x= [len(points)*special.gammainc(gamma_k,x/point_goal/gamma_theta )  for x in xrange], \
                                y=xrange, \
                                mode='lines', showlegend=False ))      

        fig.update_xaxes(title='flight number',  range=[0, math.floor((len(points) / 100)+1)*100 ])
        fig.update_yaxes(title='xc points',range=[0,500])

        img_b64 = map_fig_to_b64(fig)

        # plot #2
        fig2 = px.scatter( x=np.arange(len(points)), y=logp)
        fig2.add_trace(go.Scatter(x=[len(points)*0.5*(1.0+math.erf((math.log(x/point_goal) - mu)/sigma/math.sqrt(2.0) )) for x in xrange], \
                                y=[math.log(x/point_goal)  for x in xrange], \
                                mode='lines', showlegend=False ))
        fig2.add_trace(go.Scatter(x= [len(points)*special.gammainc(gamma_k,x/point_goal/gamma_theta )  for x in xrange], \
                                y=[math.log(x/point_goal)  for x in xrange], \
                                mode='lines', showlegend=False ))                     

        fig2.update_xaxes(title='flight number',  range=[0, math.floor((len(points) / 100)+1)*100 ])
        fig2.update_yaxes(title='log(xc points/100)',range=[-3,3])
        img2_b64 = map_fig_to_b64(fig2)

        # plot #3
        fig3 = px.scatter( x=[mu+sigma*math.sqrt(2.0)*special.erfinv(2.0*p/len(points)-1.0) for p in np.arange(len(points))], y=logp)
        fig3.add_trace(go.Scatter(x=np.arange(-3,4), y= np.arange(-3,4), mode='lines', showlegend=False ))
        fig3.update_xaxes(title='mu + sigma * sqrt2 * erf-inv (2 * flight number / number of flights + 1)',range=[-3,3])
        fig3.update_yaxes(title='log(xc points/100)',range=[-3,3])

        img3_b64 = map_fig_to_b64(fig3)

    return {
        'glider_norm': glider_norm,
        'class': g_class,
        'count': g_count,
        'pilot_count': p_count,
        'mu': mu,
        'sigma': sigma,
        'confidence': confidence,
        'flights': flights,
        'img_b64': img_b64,
        'img2_b64':img2_b64,
        'img3_b64':img3_b64
    }

async def get_comparison(year:int, compare):
        import math
        import pandas as pd
        import numpy as np   
        import plotly.express as px
        import plotly.graph_objects as go
        from scipy import special

        point_goal = 100.0

        dbName= DB_NAME_F.format(year=year)
        engine = create_engine(f'sqlite:///{dbName}')
        with engine.connect() as db:
            param = {'year':year}
            #print(param)
            comp_list = "','".join([c.replace('-',' ') for c in compare])
            df  = pd.read_sql_query(text(f"""
                        SELECT  g.glider_norm [glider]
                                    , cast(f.flight_points as float) [xc]
                                    , row_number() over(partition by g.glider_norm order by  cast(f.flight_points as float)  ) [row_num]
                        FROM flights f 
                        INNER JOIN gliders g ON g.glider=f.glider COLLATE NOCASE
                        WHERE LOWER(g.glider_norm) in ('{comp_list}') 
                    """), db, params=param)

        aggr = df.groupby(['glider'])['xc'].agg([
            ('count', len),
            ('mu', lambda value: np.mean(np.log(value/point_goal)) ),
            ('sigma', lambda value: np.std(np.log(value/point_goal)) )
        ]).to_dict()
        #print(aggr)
        df['x'] = df.apply(lambda row: math.log(row.xc/point_goal) , axis=1)
        df['y'] = df.apply(lambda row: row.row_num/aggr['count'][row.glider] , axis=1)
        df['ybar'] = df.apply(lambda row: math.sqrt(2.0)*special.erfinv(2.0*(row.row_num/aggr['count'][row.glider]-0.5)) , axis=1)

        raw=False
        if raw:
            fig = px.scatter( df, x='y', y='xc', color='glider')
            fig.update_xaxes(title='flight number/number of flights',range=[0,1])
        else:
            fig = px.scatter( df, x='ybar', y='x', color='glider')
            fig.update_yaxes(title='log(xc points/100)',range=[-3,3])
            #fig.update_yaxes(title='flight number/number of flights',range=[0,1])
            fig.update_xaxes(title='erf inv (flight number/number of flights)',range=[-3,3])

        return map_fig_to_b64(fig)


async def get_pilots():
    year = 2025 # TODO pass as param?
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
    year = 2025 # TODO pass as param?
    async with aiosqlite.connect(DB_NAME) as db:
        param = {'year': year}
        async with db.execute("""SELECT MAX(xc_rank) 
                                 FROM pilots
                                 WHERE year = :year """,param) as cursor:
            async for row in cursor:
                return row[0] or 0
        
    return 0

async def delete_pilots():
     async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""DELETE FROM pilots """)        
        await db.commit()

async def save_pilots(pilots):
    year = 2025 # TODO pass as param?
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