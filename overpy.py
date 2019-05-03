# -*- coding: utf-8 -*-
# https://janakiev.com/blog/openstreetmap-with-python-and-overpass-api/
import requests
from Bing_Aerial_API.BoundingBox import boundingBox as bb
from collections import defaultdict
import geopy.distance
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, balanced_accuracy_score

s = slice(0, 900)
df = pd.read_excel(r"Standorte_labeled.xlsx", nrows=900, index_col=0) # read first 900 rows from file
labels = df[s]["Kategorie"].copy()

replace_map = {"Sehr Gut": 1, "Gut": 2, "Mittel": 3, "Schlecht": 4}
labels.replace(replace_map, inplace=True)
labels = np.array(labels).astype(int)


def aerial_distance(elem_nodes):
    # calculate the aerial distance between a central coordinate pair and several OSM Nodes
    out = []
    for n in elem_nodes:
        if any(node['id'] == n for node in nodes):
            lat = [node['lat'] for node in nodes if node["id"] == n][0]
            lon = [node['lon'] for node in nodes if node["id"] == n][0]
            motorway_coords = (lat, lon)
            out.append(geopy.distance.distance(coords, motorway_coords).km) # aerial distance between central coords and motorway
    return out

endpoint = "https://lz4.overpass-api.de/api/interpreter"

predictions = []
# TO ADD: iterate over excel spreadsheet rows
for index, row in df.loc[s].iterrows():
    if index == s.stop:
        break

    if index % 50 == 0:
        print("Labeling row #", index)
              
    #coords = (48.993502, 12.105548) # Regensburg Bajuwarenstraße Lidl --> sehr gut
    #coords = (51.1562000000001,	12.0978200000001)
    #coords = (49.017236, 12.098673) # Regensburg Müller Drogeriemarkt Innenstadt --> schlecht
    #coords = (49.29681122396, 8.66871672003524) # --> sehr gut
    #coords = (52.1501133871833,	8.04304323827112) # --> Moderat
    
    coords = (row["Lat"], row["Lon"])
    
    _, ne, sw, _ = bb(*coords, mode=1) # we only need South-West (lower left) and North-East (upper right)
    
    #print(ne, sw)
    
    bounding_box = "{sw_lat},{sw_lng},{ne_lat},{ne_lng}".format(sw_lat=sw[0], sw_lng=sw[1], ne_lat=ne[0], ne_lng=ne[1])  
    #query = """
    #           [out:json][timeout:25];
    #// gather results
    #(
    #  // query part for: “highway=*”
    #  node["highway"="motorway_link"]({bbox});
    #  way["highway"="motorway_link"]({bbox});
    #  relation["highway"="motorway_link"]({bbox});
    #  
    #  node["highway"="motorway"]({bbox});
    #  way["highway"="motorway"]({bbox});
    #  relation["highway"="motorway"]({bbox});
    #  
    #  node["highway"="tertiary"]({bbox});
    #  way["highway"="tertiary"]({bbox});
    #  relation["highway"="tertiary"]({bbox});
    #  
    #  node["highway"="residential"]({bbox});
    #  way["highway"="residential"]({bbox});
    #  relation["highway"="residential"]({bbox});
    #  
    #  node["landuse"="residential"]({bbox});
    #  way["landuse"="residential"]({bbox});
    #  relation["landuse"="residential"]({bbox});
    #  
    #  node["landuse"="commercial"]({bbox});
    #  way["landuse"="commercial"]({bbox});
    #  relation["landuse"="commercial"]({bbox});
    #  
    #  node["landuse"="industrial"]({bbox});
    #  way["landuse"="industrial"]({bbox});
    #  relation["landuse"="industrial"]({bbox});
    #  
    #  node["building"="commercial"]({bbox});
    #  way["building"="commercial"]({bbox});
    #  relation["building"="commercial"]({bbox});
    #  
    #  node["building"="warehouse"]({bbox});
    #  way["building"="warehouse"]({bbox});
    #  relation["building"="warehouse"]({bbox});
    #);
    #out center;
    #""".format(bbox=bounding_box)
    
    query = """
            [out:json][timeout:25];
            (
            node({sw_lat},{sw_lng},{ne_lat},{ne_lng});
            way({sw_lat},{sw_lng},{ne_lat},{ne_lng});
            );
            out;
            """.format(sw_lat=sw[0], sw_lng=sw[1], ne_lat=ne[0], ne_lng=ne[1])            
    
    #print(query)
    
    response = requests.get(endpoint, 
                            params={'data': query})
    data = response.json()
    
    highways = defaultdict(int)
    buildings = defaultdict(int)
    landuse = defaultdict(int)
    
    motlink_dist = []
    tert_dist = []
    sec_dist = []
    pri_dist = []
    
    nodes = [x for x in data["elements"] if "node" in x.values()]
    elem = [x for x in data["elements"] if "way" in x.values()]
    for e in elem:
        if "tags" in e:
            tags = e["tags"] # extract tags
            try: # search for every highway/road
                highways[tags["highway"]] += 1
                # look for motorway_links (Autobahnauffahrten) and calculate aerial distance
                if tags["highway"] == "motorway_link":
                    motlink_dist = motlink_dist + aerial_distance(e["nodes"])
                # look for tertiary roads and calculate aerial distance
                if tags["highway"] == "tertiary":
                    tert_dist = tert_dist + aerial_distance(e["nodes"])
                if tags["highway"] == "secondary":
                    sec_dist = sec_dist + aerial_distance(e["nodes"])
                if tags["highway"] == "primary":
                    pri_dist = pri_dist + aerial_distance(e["nodes"])
            except:
                pass
            
            try: # search for every building
                buildings[tags["building"]] += 1
            except:
                pass
            
            try: # search for every landuse categorization
                landuse[tags["landuse"]] += 1
            except:
                pass
    
    if len(motlink_dist) > 0:
        min_motway_link_dist = min(motlink_dist) # average distance to next motorway_link
    else:
        min_motway_link_dist = 100
    if len(tert_dist) > 0:
        min_tert_dist = min(tert_dist)
    else:
        min_tert_dist = 100
    if len(sec_dist) > 0:
        min_sec_dist = min(sec_dist)
    else:
        min_sec_dist = 100
    if len(pri_dist) > 0:
        min_pri_dist = min(pri_dist)
    else:
        min_pri_dist = 100

          
    # CLASSIFICATION
    if(
        buildings["warehouse"] > 0 or
        landuse.get("residential") is None or
        (
        landuse["residential"] < landuse["industrial"] and 
        landuse["residential"] < landuse["commercial"]
        ) or
        min_motway_link_dist <= 0.15 or
        min_tert_dist <= 0.1 or
        min_sec_dist <= 0.1 or
        min_pri_dist <= 0.1
        ):
        predictions.append("Sehr Gut")
    elif(
        (highways["tertiary"] > 0 or highways["secondary"] > 0 or highways["primary"] > 0 or highways["service"] >= 10) and
        (buildings["yes"] <= 20) or
        (min_motway_link_dist <= 0.3 or
        min_tert_dist <= 0.3 or
        min_sec_dist <= 0.3 or
        min_pri_dist <= 0.3
        )
        ):
        predictions.append("Gut")
    elif(
        (buildings["yes"] <= 50) or
        (min_motway_link_dist <= 0.5 or
        min_tert_dist <= 0.5 or
        min_sec_dist <= 0.5 or
        min_pri_dist <= 0.5
        )
        ):
        predictions.append("Mittel")
    else:
        predictions.append("Schlecht")
#    if(
#        (highways["residential"] > highways["tertiary"]) and
#        (highways["residential"] > highways["unclassified"]) and
#        (landuse["residential"] > landuse["commercial"]) and
#        (landuse["residential"] > landuse["industrial"]) or
#        (buildings["yes"] > 100)
#        ):
#        print("Schlecht")
#        predictions.append("Schlecht")
#        continue
#    
#    elif(
#       (buildings["yes"] <= 100 and buildings["yes"] > 50) or
#       (min_tert_dist > 0.2 and highways["service"] < 10)
#       ):
#        print("Moderat")
#        predictions.append("Mittel")
#        continue
#    
#    elif (
#        landuse.get("residential") is None or
#        landuse["residential"] < landuse["industrial"] or 
#        landuse["residential"] < landuse["commercial"] or
#        min_motway_link_dist <= 0.15 or
#        min_tert_dist <= 0.1
#        ):
#        print("Sehr gut")
#        predictions.append("Sehr Gut")
#    else:
#        predictions.append("Gut")
        
        
# Accuracy
pred_replaced = pd.DataFrame(predictions, columns=["Kategorie"]).replace(replace_map).squeeze()
pred_replaced = np.array(pred_replaced).astype(int)
print(classification_report(labels, pred_replaced, target_names=[x for x in replace_map.keys()]))
print("Accuracy: ", balanced_accuracy_score(labels, pred_replaced))