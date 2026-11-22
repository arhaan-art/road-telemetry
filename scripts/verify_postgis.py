"""Spatial verification against PostGIS: counts, bbox query, nearest segment to a Connaught Place point, defects within radius."""
import os, sys
sys.path.insert(0,".")
os.environ.setdefault("DATABASE_URL","postgresql://rtadmin@127.0.0.1:5433/road_telemetry")
import psycopg
from psycopg.rows import dict_row
c=psycopg.connect(os.environ["DATABASE_URL"],row_factory=dict_row)
q=lambda sql,args=(): c.execute(sql,args).fetchone()
print("postgis",q("SELECT PostGIS_Version() v")["v"])
print("counts",q("SELECT (SELECT COUNT(*) FROM road_segments) seg,(SELECT COUNT(*) FROM buildings) bld,(SELECT COUNT(*) FROM trees) tr,(SELECT COUNT(*) FROM defects) def") )
print("segments_in_bbox",q("SELECT COUNT(*) n FROM road_segments WHERE geom && ST_MakeEnvelope(77.21,28.625,77.225,28.638,4326)")["n"])
print("nearest_segment_to_CP",q("""SELECT name, ROUND(ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(77.2195,28.6315),4326)::geography)::numeric,1) dist_m
  FROM road_segments ORDER BY geom <-> ST_SetSRID(ST_MakePoint(77.2195,28.6315),4326) LIMIT 1"""))
print("buildings_within_300m_CP",q("SELECT COUNT(*) n FROM buildings WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(77.2195,28.6315),4326)::geography, 300)")["n"])
print("spatial_index_present",q("SELECT COUNT(*) n FROM pg_indexes WHERE indexname IN ('seg_gist','defects_gist','buildings_gist')")["n"])
