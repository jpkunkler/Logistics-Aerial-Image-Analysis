# -*- coding: utf-8 -*-
# https://janakiev.com/blog/openstreetmap-with-python-and-overpass-api/
import requests
from Bing_Aerial_API.BoundingBox import boundingBox as bb

endpoint = "https://lz4.overpass-api.de/api/interpreter"

#coords = (48.993502, 12.105548)
coords = (51.1562000000001,	12.0978200000001)

_, ne, sw, _ = bb(*coords, mode=1) # we only need South-West (lower left) and North-East (upper right)

print(ne, sw)

bounding_box = "{sw_lat},{sw_lng},{ne_lat},{ne_lng}".format(sw_lat=sw[0], sw_lng=sw[1], ne_lat=ne[0], ne_lng=ne[1])  
query = """
           [out:json][timeout:25];
// gather results
(
  // query part for: “highway=*”
  node["highway"="motorway_link"]({bbox});
  way["highway"="motorway_link"]({bbox});
  relation["highway"="motorway_link"]({bbox});
  
  node["highway"="motorway"]({bbox});
  way["highway"="motorway"]({bbox});
  relation["highway"="motorway"]({bbox});
  
  node["highway"="tertiary"]({bbox});
  way["highway"="tertiary"]({bbox});
  relation["highway"="tertiary"]({bbox});
  
  node["highway"="residential"]({bbox});
  way["highway"="residential"]({bbox});
  relation["highway"="residential"]({bbox});
  
  node["landuse"="residential"]({bbox});
  way["landuse"="residential"]({bbox});
  relation["landuse"="residential"]({bbox});
  
  node["building"="commercial"]({bbox});
  way["building"="commercial"]({bbox});
  relation["building"="commercial"]({bbox});
);
out center;
""".format(bbox=bounding_box)

#query = """
#        [out:json];
#        node({sw_lat},{sw_lng},{ne_lat},{ne_lng});
#        out center;
#        """.format(sw_lat=sw[0], sw_lng=sw[1], ne_lat=ne[0], ne_lng=ne[1])            

#print(query)

response = requests.get(endpoint, 
                        params={'data': query})
data = response.json()