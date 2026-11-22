# Local PostgreSQL+PostGIS (no Docker)
Provisioned and verified 2026-11-22 on Amazon Linux 2023:
1. `sudo dnf install -y postgresql15-server postgresql15-devel postgresql15-server-devel geos-devel proj-devel libxml2-devel json-c-devel gcc make` (AL2023 ships PG 15.20 + GEOS/PROJ but no PostGIS package).
2. Build PostGIS 3.4.3 from source: download from download.osgeo.org, `./configure --with-pgconfig=/usr/bin/pg_config --without-raster --without-protobuf --without-topology --without-sfcgal && make -j4 && sudo make install`.
3. `initdb -D /tmp/rt-pgdata -U rtadmin --auth=trust; pg_ctl -D /tmp/rt-pgdata -o "-p 5433 -k /tmp" start; createdb road_telemetry`.
4. `psql $DATABASE_URL -f migrations/001_postgis.sql -f migrations/002_network_endpoints.sql` (DATABASE_URL=postgresql://rtadmin@127.0.0.1:5433/road_telemetry).
5. `DATABASE_URL=... python3 scripts/migrate_sqlite_to_postgres.py` then `python3 scripts/verify_postgis.py`.
6. Run app with DATABASE_URL set; without it the app keeps the SQLite fallback so tests/dev stay zero-dependency.
Verified: PostGIS 3.4 (GEOS/PROJ), 7,296 segments / 1,473 buildings (6 degenerate footprints dropped) / 74 trees migrated, GiST indexes present, nearest-segment and ST_DWithin queries correct, and user+defect+routing survive an app restart.
