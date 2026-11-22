-- Endpoint/node columns so the routing graph can be rebuilt from PostGIS (run after 001).
ALTER TABLE road_segments ADD COLUMN IF NOT EXISTS from_id TEXT;
ALTER TABLE road_segments ADD COLUMN IF NOT EXISTS to_id TEXT;
ALTER TABLE road_segments ADD COLUMN IF NOT EXISTS from_lat DOUBLE PRECISION;
ALTER TABLE road_segments ADD COLUMN IF NOT EXISTS from_lon DOUBLE PRECISION;
ALTER TABLE road_segments ADD COLUMN IF NOT EXISTS to_lat DOUBLE PRECISION;
ALTER TABLE road_segments ADD COLUMN IF NOT EXISTS to_lon DOUBLE PRECISION;
ALTER TABLE road_segments ADD COLUMN IF NOT EXISTS highway TEXT;
ALTER TABLE road_segments ADD COLUMN IF NOT EXISTS distance_m DOUBLE PRECISION;
ALTER TABLE defects ADD COLUMN IF NOT EXISTS lat DOUBLE PRECISION;
ALTER TABLE defects ADD COLUMN IF NOT EXISTS lon DOUBLE PRECISION;
CREATE INDEX IF NOT EXISTS segments_from_idx ON road_segments(from_id);
CREATE INDEX IF NOT EXISTS segments_to_idx ON road_segments(to_id);
