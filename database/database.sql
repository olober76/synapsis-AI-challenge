-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- ========================
-- TABLE: areas
-- ========================
CREATE TABLE areas (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    geom GEOMETRY(POLYGON, 0) NOT NULL, 
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_areas_updated_at
BEFORE UPDATE ON areas
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    object_id TEXT NOT NULL,
    camera_id TEXT,
    area_id INTEGER REFERENCES areas(id) ON DELETE SET NULL,
    bbox JSONB NOT NULL,
    center_point GEOMETRY(POINT, 0),
    confidence FLOAT,
    entered BOOLEAN DEFAULT FALSE,
    exited BOOLEAN DEFAULT FALSE
);


CREATE TABLE counts (
    id SERIAL PRIMARY KEY,
    area_id INTEGER REFERENCES areas(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    count_in INTEGER DEFAULT 0,
    count_out INTEGER DEFAULT 0
);


INSERT INTO areas (name, geom) VALUES (
    'Zona A (pixel)',
    ST_GeomFromText('POLYGON((100 200, 300 200, 300 400, 100 400, 100 200))', 0)
);


INSERT INTO detections (timestamp, object_id, camera_id, area_id, bbox, center_point, confidence, entered)
VALUES (
    NOW(), 
    'track_001', 
    'cam_01', 
    1,
    '{"x":120, "y":220, "w":40, "h":80}',
    ST_SetSRID(ST_MakePoint(140, 260), 0),
    0.91,
    TRUE
);


INSERT INTO counts (area_id, timestamp, count_in, count_out)
VALUES (1, NOW(), 1, 0);
