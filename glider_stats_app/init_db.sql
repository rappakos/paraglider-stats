CREATE TABLE IF NOT EXISTS pilots
               (
                [year] int not null,
                xc_rank int not null, 
                username, 
                pilot_id);

CREATE TABLE IF NOT EXISTS flights
            (pilot_id, flight_id, launch,flight_type,flight_length,flight_points, glider, details);

CREATE TABLE IF NOT EXISTS gliders
            (glider TEXT PRIMARY KEY,class TEXT, glider_norm TEXT,UNIQUE (glider COLLATE NOCASE));