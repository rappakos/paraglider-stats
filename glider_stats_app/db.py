# db.py
import aiosqlite

DB_NAME = './glider_stats.db'
INIT_SCRIPT = './glider_stats_app/init_db.sql'

async def setup_db(app):
    app['DB_NAME'] = DB_NAME
    async with aiosqlite.connect(DB_NAME) as db:
        # only test
        async with db.execute("SELECT 'check'") as cursor:
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