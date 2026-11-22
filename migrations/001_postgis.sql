-- Road Telemetry PostGIS schema (production). Run: psql $DATABASE_URL -f migrations/001_postgis.sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY,email TEXT UNIQUE NOT NULL,pw_hash TEXT NOT NULL,name TEXT,role TEXT DEFAULT 'rider',created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS road_segments(id TEXT PRIMARY KEY,name TEXT,geom geometry(LineString,4326) NOT NULL,oneway BOOLEAN DEFAULT false,vehicle_access TEXT DEFAULT 'all',shade_frac REAL DEFAULT 0,pothole_penalty REAL DEFAULT 0,source TEXT DEFAULT 'osm');
CREATE INDEX IF NOT EXISTS seg_gist ON road_segments USING GIST(geom);
CREATE TABLE IF NOT EXISTS defects(id SERIAL PRIMARY KEY,geom geometry(Point,4326) NOT NULL,category TEXT,severity INT CHECK(severity BETWEEN 1 AND 5),status TEXT DEFAULT 'unverified',confidence REAL,reports INT DEFAULT 1,source TEXT,segment_id TEXT REFERENCES road_segments(id),created_at TIMESTAMPTZ DEFAULT now());
CREATE INDEX IF NOT EXISTS defects_gist ON defects USING GIST(geom);
CREATE TABLE IF NOT EXISTS telemetry_events(id SERIAL PRIMARY KEY,device_id TEXT,geom geometry(Point,4326),payload JSONB,created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS buildings(id SERIAL PRIMARY KEY,geom geometry(Polygon,4326),height_m REAL,height_confidence REAL DEFAULT 0.5);
CREATE INDEX IF NOT EXISTS buildings_gist ON buildings USING GIST(geom);
CREATE TABLE IF NOT EXISTS trees(id SERIAL PRIMARY KEY,geom geometry(Polygon,4326),canopy_confidence REAL DEFAULT 0.5);
CREATE TABLE IF NOT EXISTS thermal_estimates(id SERIAL PRIMARY KEY,segment_id TEXT REFERENCES road_segments(id),valid_at TIMESTAMPTZ,utci_proxy REAL,shade_frac REAL,confidence REAL);
CREATE TABLE IF NOT EXISTS audit(id SERIAL PRIMARY KEY,entity TEXT,entity_id INT,action TEXT,actor TEXT,created_at TIMESTAMPTZ DEFAULT now());
