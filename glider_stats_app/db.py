# db.py
import aiosqlite

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