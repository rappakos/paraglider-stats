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


CREATE TEMPORARY TABLE temp_gliders(glider, class, glider_norm);
INSERT INTO temp_gliders(glider,class,glider_norm)
VALUES
('OZONE Alpina 4','C','OZONE Alpina 4'),
('OZONE Photon','C','OZONE Photon'),
('AIRDESIGN Volt 4','C','AIRDESIGN Volt 4'),
('NIVIUK Artik R','C','NIVIUK Artik R'),
('OZONE Delta 4','C','OZONE Delta 4'),
('ADVANCE Sigma 11','C','ADVANCE Sigma 11'),
('NOVA MENTOR 7 light','B','NOVA MENTOR 7 light'),
('FLOW PARAGLIDERS Fusion','C','FLOW PARAGLIDERS Fusion'),
('NIVIUK Artik 6','C','NIVIUK Artik 6'),
('ADVANCE Iota DLS','B','ADVANCE Iota DLS'),
('OZONE Rush 6','B','OZONE Rush 6'),
('SUPAIR Savage','C','SUPAIR Savage'),
('SKYWALK Mint','C','SKYWALK Mint'),
('GIN GLIDERS Bonanza 2','C','GIN GLIDERS Bonanza 2'),
('GIN GLIDERS Bonanza 3','C','GIN GLIDERS Bonanza 3'),
('OZONE SwiftSix','B','OZONE SwiftSix'),
('OZONE Delta 3','C','OZONE Delta 3'),
('OZONE Alpina 3','C','OZONE Alpina 3'),
('PHI Maestro 2 light','C','PHI Maestro 2 light');

INSERT INTO gliders (glider, class, glider_norm)
SELECT t.glider, t.class, t.glider_norm
FROM temp_gliders t
WHERE NOT EXISTS (
    SELECT 1 FROM gliders g WHERE g.glider=t.glider COLLATE NOCASE
);
