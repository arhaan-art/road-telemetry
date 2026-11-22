import heapq, math
PRESETS={"fastest":(1.0,0.0,0.0),"smoothest":(0.2,0.8,0.0),"coolest":(0.2,0.0,0.8),"balanced":(0.34,0.33,0.33)}
def normalise_weights(wt,wp,wh):
    s=wt+wp+wh
    if s<=0: return (0.34,0.33,0.33)
    return (wt/s,wp/s,wh/s)
class Graph:
    def __init__(self): self.adj={}; self.edges={}
    def add_node(self,n): self.adj.setdefault(n,[])
    def add_edge(self,u,v,**kw):
        e={"u":u,"v":v,"distance_m":kw.get("distance_m",100),"speed_kmh":kw.get("speed_kmh",30),
           "pothole_penalty":kw.get("pothole_penalty",0.0),"shade_frac":kw.get("shade_frac",0.3),
           "name":kw.get("name",""),"lat_u":kw.get("lat_u"),"lon_u":kw.get("lon_u"),"lat_v":kw.get("lat_v"),"lon_v":kw.get("lon_v")}
        e["travel_s"]=e["distance_m"]/(e["speed_kmh"]/3.6)
        self.edges[(u,v)]=e; self.adj.setdefault(u,[]).append((v,e)); self.add_node(v); return e
    def edge_cost(self,e,weights,thermal_norm=1.0):
        wt,wp,wh=weights
        T=e["travel_s"]/600.0  # normalised per 10 min
        P=e["pothole_penalty"]
        H=(1-e["shade_frac"])*e["travel_s"]/600.0*thermal_norm
        return max(0.0, wt*T+wp*P+wh*H)  # live costs non-negative
def _path(prev,dst):
    p=[]; c=dst
    while c is not None: p.append(c); c=prev.get(c)
    return list(reversed(p))
def dijkstra(g,src,dst,weights):
    dist={src:0.0}; prev={src:None}; pq=[(0,src)]
    while pq:
        d,u=heapq.heappop(pq)
        if d>dist.get(u,1e18): continue
        if u==dst: break
        for v,e in g.adj.get(u,[]):
            nd=d+g.edge_cost(e,weights)
            if nd<dist.get(v,1e18): dist[v]=nd; prev[v]=u; heapq.heappush(pq,(nd,v))
    return (dist.get(dst),_path(prev,dst)) if dst in dist else (None,[])
def astar(g,src,dst,weights,coords):
    def h(n):
        if n not in coords or dst not in coords: return 0
        a,b=coords[n],coords[dst]; return math.hypot(a[0]-b[0],a[1]-b[1])/100000.0
    gs={src:0.0}; prev={src:None}; pq=[(h(src),src)]
    while pq:
        f,u=heapq.heappop(pq)
        if u==dst: break
        for v,e in g.adj.get(u,[]):
            nd=gs[u]+g.edge_cost(e,weights)
            if nd<gs.get(v,1e18): gs[v]=nd; prev[v]=u; heapq.heappush(pq,(nd+h(v),v))
    return (gs.get(dst),_path(prev,dst)) if dst in gs else (None,[])
def bellman_ford(g,src):
    nodes=list(g.adj); dist={n:float("inf") for n in nodes}; dist[src]=0.0; prev={src:None}
    for _ in range(len(nodes)-1):
        for (u,v),e in g.edges.items():
            w=g.edge_cost(e,(1,0,0))
            if dist[u]+w<dist[v]: dist[v]=dist[u]+w; prev[v]=u
    neg=any(dist[u]+g.edge_cost(e,(1,0,0))<dist[v] for (u,v),e in g.edges.items())
    return dist,prev,neg
def floyd_warshall(g):
    nodes=list(g.adj); idx={n:i for i,n in enumerate(nodes)}; n=len(nodes)
    D=[[float("inf")]*n for _ in range(n)]
    for i in range(n): D[i][i]=0
    for (u,v),e in g.edges.items(): D[idx[u]][idx[v]]=g.edge_cost(e,(1,0,0))
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if D[i][k]+D[k][j]<D[i][j]: D[i][j]=D[i][k]+D[k][j]
    return nodes,D
def kruskal(nodes,edges):
    parent={n:n for n in nodes}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    mst=[]; total=0.0
    for w,u,v in sorted(edges):
        ru,rv=find(u),find(v)
        if ru!=rv: parent[ru]=rv; mst.append((u,v,w)); total+=w
    return mst,total
def summarise(g,path,weights,thermal_by_edge=None):
    dist=dur=exp=0.0; segs=[]
    for a,b in zip(path,path[1:]):
        e=g.edges[(a,b)]; dist+=e["distance_m"]; dur+=e["travel_s"]
        utci=(thermal_by_edge or {}).get((a,b),32.0)
        dose=max(0,utci-26)*e["travel_s"]; exp+=dose
        segs.append({"from":a,"to":b,"name":e["name"],"distance_m":e["distance_m"],"travel_s":round(e["travel_s"],1),
                     "shade_frac":e["shade_frac"],"pothole_penalty":e["pothole_penalty"],"utci_proxy_c":utci,"exposure_dose":round(dose,1)})
    return {"path":path,"distance_m":round(dist,1),"duration_s":round(dur,1),"cumulative_exposure":round(exp,1),"segments":segs}
def should_switch(old_cost,new_cost,threshold=0.05):
    """Hysteresis: avoid route flapping on minor differences."""
    if old_cost is None: return True
    return new_cost < old_cost*(1-threshold)
def yen_k_shortest(g,src,dst,weights,k=3):
    first_cost,first=dijkstra(g,src,dst,weights)
    if not first: return []
    results=[(first_cost,first)]; candidates=[]
    def remove_edge(u,v):
        e=g.edges.pop((u,v),None)
        g.adj[u]=[(vv,ee) for vv,ee in g.adj.get(u,[]) if vv!=v]
        return e
    def restore_edge(u,v,e):
        if e is None: return
        g.edges[(u,v)]=e; g.adj[u].append((v,e))
    for kk in range(1,k):
        prev_path=results[-1][1]
        for i in range(len(prev_path)-1):
            spur=prev_path[i]; root=prev_path[:i+1]
            removed=[]
            for c,p in results:
                if len(p)>i and p[:i+1]==root and (p[i],p[i+1]) in g.edges: removed.append((p[i],p[i+1],remove_edge(p[i],p[i+1])))
            saved_adj={n:list(g.adj.get(n,[])) for n in root[:-1]}
            for n in root[:-1]: g.adj[n]=[]
            cost,spur_path=dijkstra(g,spur,dst,weights)
            for n,adj in saved_adj.items(): g.adj[n]=adj
            for u,v,e in removed: restore_edge(u,v,e)
            if spur_path:
                total=root[:-1]+spur_path
                if total not in [p for _,p in results+candidates]:
                    tc=sum(g.edge_cost(g.edges[(a,b)],weights) for a,b in zip(total,total[1:])); candidates.append((tc,total))
        if not candidates: break
        candidates.sort(key=lambda x:x[0]); results.append(candidates.pop(0))
    return results
