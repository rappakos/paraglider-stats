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
INSERT INTO temp_gliders(glider,glider_norm,class)
VALUES
('OZONE Alpina 4','OZONE Alpina 4','C'),
('OZONE Photon','OZONE Photon','C'),
('AIRDESIGN Volt 4','AIRDESIGN Volt 4','C'),
('NIVIUK Artik R','NIVIUK Artik R','C'),
('OZONE Delta 4','OZONE Delta 4','C'),
('ADVANCE Sigma 11','ADVANCE Sigma 11','C'),
('NOVA MENTOR 7 light','NOVA MENTOR 7 light','B'),
('FLOW PARAGLIDERS Fusion','FLOW Fusion','C'),
('NIVIUK Artik 6','NIVIUK Artik 6','C'),
('ADVANCE Iota DLS','ADVANCE Iota DLS','B'),
('OZONE Rush 6','OZONE Rush 6','B'),
('SUPAIR Savage','SUPAIR Savage','C'),
('SKYWALK Mint','SKYWALK Mint','C'),
('GIN GLIDERS Bonanza 2','GIN Bonanza 2','C'),
('GIN GLIDERS Bonanza 3','GIN Bonanza 3','C'),
('OZONE SwiftSix','OZONE SwiftSix','B'),
('OZONE Delta 3','OZONE Delta 3','C'),
('OZONE Alpina 3','OZONE Alpina 3','C'),
('PHI Maestro 2 light','PHI Maestro 2 light','B'),
('OZONE Swift 5','OZONE Swift 5','B'),
('ADVANCE Sigma 10','ADVANCE Sigma 10','C'),
('GIN GLIDERS Camino','GIN Camino','C'),
('GIN GLIDERS Explorer 2','GIN Explorer 2','B'),
('PHI Allegro X-alps','PHI Allegro X-alps','C'),
('NIVIUK Ikuma 2','NIVIUK Ikuma 2','B'),
('SKYWALK Chili 5','SKYWALK Chili 5','B'),
('OZONE Rush 5','OZONE Rush 5','B'),
('PHI Maestro 2','PHI Maestro 2','B'),
('BGD Base 2','BGD Base 2','B');

--DELETE FROM gliders;

INSERT INTO gliders (glider, class, glider_norm)
SELECT t.glider, t.class, t.glider_norm
FROM temp_gliders t
WHERE NOT EXISTS (
    SELECT 1 FROM gliders g WHERE g.glider=t.glider COLLATE NOCASE
);
