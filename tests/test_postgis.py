import os, sys
sys.path.insert(0,".")
import pytest
pytestmark=pytest.mark.skipif(not os.environ.get("DATABASE_URL","").startswith("postgres"),reason="PostGIS integration: set DATABASE_URL")
def test_pg_counts_and_spatial():
    from backend import db as store
    seg,bld,tr=store.load_network(); assert len(seg)>7000 and len(bld)>1000 and len(tr)>50
    assert seg[0]["from_id"] and seg[0]["name"]
def test_pg_route_real_delhi():
    from backend import db as store
    from backend.routing.real_route import timed_route_real
    from datetime import datetime,timezone
    seg,bld,tr=store.load_network()
    out=timed_route_real(seg,bld,tr,(28.6335703,77.2206283),(28.631252,77.2224344),"coolest",depart=datetime(2026,6,1,7,30,tzinfo=timezone.utc),temp_c=41)
    assert out and out["segments"][0]["solar"]["elevation_deg"]>0 and out["network"]=="real_osm_persisted"
