#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRIPT FOR GENERATING NATIONWIDE NETWORK TOPOLOGIES FOR LABORATORY USE
"""

import argparse
import os
import random
import math
import csv
import unicodedata
import json
from collections import defaultdict
import datetime
import sys

# Script version
VERSION = "1.0.1"

def load_config(config_path):
    """Loads configuration from a JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
            # Convert PTT coordinates to tuples
            config['PTTS'] = [tuple(item) for item in config['PTTS']]
            
            # Convert cities per state (UF) to lists of tuples
            for uf in config['CIDADES_UF']:
                config['CIDADES_UF'][uf] = [tuple(city) for city in config['CIDADES_UF'][uf]]
                
            return config
    except Exception as e:
        print(f"ERROR: Failed to load configuration file: {str(e)}")
        sys.exit(1)

def remove_accents(text):
    """Removes accents, special characters and normalizes strings"""
    if not text:
        return ""
    
    # Convert to string if not already
    text = str(text)
    
    # Normalize and remove non-ASCII characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove remaining special characters
    text = ''.join(c for c in text if c.isalnum() or c in [' ', '.', '-'])
    return text

def normalize_str(s):
    """Normalizes string by removing accents and spaces"""
    s = ''.join(c for c in unicodedata.normalize('NFD', s) 
               if unicodedata.category(c) != 'Mn')
    s = s.replace(' ', '').replace("'", "").replace("-", "")
    return s[:10].upper()

def decimal_to_dms(decimal, coord_type):
    """Converts decimal coordinates to DMS format"""
    if decimal >= 0:
        direction = 'N' if coord_type == 'lat' else 'E'
    else:
        direction = 'S' if coord_type == 'lat' else 'W'
    
    decimal = abs(decimal)
    degrees = int(decimal)
    minutes_decimal = (decimal - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    # Handle overflow
    if round(seconds, 2) >= 60.00:
        minutes += 1
        seconds = 0
        if minutes == 60:
            degrees += 1
            minutes = 0
    
    return f"{degrees}.{minutes}.{seconds:.2f}{direction}"

def generate_site_id(uf, city, element_type, counter, abbreviations):
    """Generates a unique siteid for the element"""
    city_norm = normalize_str(city)
    abrev = abbreviations[element_type]
    return f"{uf}{city_norm}0{abrev}{counter:03d}"

def get_region(uf, regions_config):
    """Gets the geographic region based on the UF (state)"""
    for region, ufs_region in regions_config.items():
        if uf in ufs_region:
            return region
    return "Unknown"

def geographic_distance(lat1, lon1, lat2, lon2):
    """Calculates approximate distance between two coordinates (km)"""
    # Conversion factor from degrees to km
    km_per_degree = 111.32
    delta_lat = (lat2 - lat1) * km_per_degree
    delta_lon = (lon2 - lon1) * km_per_degree * abs(math.cos(math.radians((lat1+lat2)/2)))
    return math.sqrt(delta_lat**2 + delta_lon**2)

def generate_ptt_site_id(city):
    """Generates a siteid for PTT elements (format: PTT_CITYNORM)"""
    city_norm = normalize_str(city).replace(" ", "").upper()
    return f"PTT_{city_norm}"

def main():
    
    help_text = f"""
NETWORK ELEMENTS AND CONNECTIONS GENERATOR FOR NATIONAL BACKBONE LABORATORY {VERSION}
================================================================================

⭐ OVERVIEW
-----------
Generates CSV files for hierarchical backbone network modeling:
  elements.csv    -> Equipment and attributes
  connections.csv -> Interconnections between devices
  locations.csv   -> Geographic data (DMS coordinates)

🚀 HOW TO USE
-------------
Basic format:
  python backbone-network-topology-generator.py [OPTIONS]

Examples:
  1. Default topology (300 elements):
     python backbone-network-topology-generator.py
  
  2. Custom topology (500 elements):
     python backbone-network-topology-generator.py -e 500 -c my_config.json

⚙️ ARGUMENTS:
-------------
  -e  Total number of elements (30-1000, default: 300)
  -c  Path to configuration file (default: config.json)

🔧 ADVANCED CUSTOMIZATION (config.json)
---------------------------------------
Customize proportions and hierarchy by editing:
1. PROPORCAO_CAMADAS (Layer Proportion):
   • Adjust % of each layer (e.g.: {{"RTIC": 0.03}} = 3% of RTICs)
   • Layers: RTIC, RTRR, RTPR, RTED, SWAC

2. PROPORCOES_REGIAO (Regional Proportion):
   • Redistribute elements by region (e.g.: {{"Sudeste": 0.5}} = 50% in Southeast)
   • Regions: Norte, Nordeste, Centro-Oeste, Sudeste, Sul

3. REGIOES_HIERARQUIA (Regional Hierarchy):
   • Define strategic hubs and sub-regions

📂 GENERATED OUTPUT
-------------------
    Folder: TOPOLOGY_[QTY]_[TIMESTAMP]/
    ├── elements.csv    # Equipment (siteid, layer, level)
    ├── connections.csv # Connections (endpoint-a, endpoint-b, type)
    ├── locations.csv   # Coordinates (DMS) and region
    └── summary.txt     # Topology statistics

🏗️ NETWORK HIERARCHY (5 Layers)
------------------------------
1. INNER-CORE (RTIC: 2%): High-capacity core.
2. REFLECTOR (RTRR: 3%): Regional aggregation.
3. PEERING (RTPR: 3%): IXP interconnection.
4. EDGE (RTED: 12%): Network edge.
5. METRO (SWAC: 80%): Metropolitan access.

🔍 UPDATES AND DOCUMENTATION:
---------------------------
🔗 Repository - Follow on GitHub for new versions and updates

Generate topologies dynamically
https://github.com/flashbsb/network-topology-generator

Execute massive commands simply and generate connection information between network elements
https://github.com/flashbsb/network-data-extractor

Dimension backbone topologies for testing:
https://github.com/flashbsb/backbone-network-topology-generator
"""
    # Create parser with full description
    parser = argparse.ArgumentParser(
        description=help_text,
        formatter_class=argparse.RawTextHelpFormatter
    )   
    
    parser.add_argument(
        '-e', 
        type=int, 
        default=300,
        help='Total number of elements (default: 300)'
    )
    
    parser.add_argument(
        '-c',
        type=str,
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    args = parser.parse_args()

    if args.e < 30:
        print("ERROR: Minimum quantity of elements is 30")
        sys.exit(1)
    
    # 1. Load configuration
    config = load_config(args.c)
    
    # Extract configurations
    LAYER_PROPORTION = config["PROPORCAO_CAMADAS"]
    REGIONAL_PROPORTION = config["PROPORCOES_REGIAO"]
    REGIONAL_HIERARCHY = config["REGIOES_HIERARQUIA"]
    ABBREVIATIONS = config["ABREVIACOES"]
    REGIONS = config["REGIOES"]
    PTT_DATA = config["PTTS"]
    CITIES_UF = config["CIDADES_UF"]
    
    # Calculate required minimums based on hierarchy
    min_rtics = 0
    min_rtrrs = 0
    for region, data in REGIONAL_HIERARCHY.items():
        min_rtics += len(data["hubs"])
        min_rtrrs += len(data["sub-regioes"])
    
    # Calculate quantities based on proportions
    actual_dist = {
        "RTIC": max(min_rtics, round(LAYER_PROPORTION["RTIC"] * args.e)),
        "RTRR": max(min_rtrrs, round(LAYER_PROPORTION["RTRR"] * args.e)),
        "RTPR": round(LAYER_PROPORTION["RTPR"] * args.e),
        "RTED": round(LAYER_PROPORTION["RTED"] * args.e),
        "SWAC": round(LAYER_PROPORTION["SWAC"] * args.e)
    }
    
    # Adjust for rounding differences
    calculated_total = sum(actual_dist.values())
    diff = args.e - calculated_total
    if diff != 0:
        # Adjust in the layer with the highest proportion
        adjustment_layer = max(LAYER_PROPORTION, key=LAYER_PROPORTION.get)
        actual_dist[adjustment_layer] += diff
    
    # Ensure RTED is even for pairing
    if actual_dist["RTED"] % 2 != 0:
        actual_dist["RTED"] += 1
    
    # 2. Generate PTT elements
    ptt_elements = []
    for ptt in PTT_DATA:
        ptt_city = ptt[0]
        ptt_uf = ptt[1]
        ptt_lat = ptt[2]
        ptt_lon = ptt[3]
        
        # Add jitter to avoid exact overlapping
        lat_jitter = ptt_lat + random.uniform(-0.0005, 0.0005)
        lon_jitter = ptt_lon + random.uniform(-0.0005, 0.0005)
        
        ptt_elements.append({
            "element": f"PTT-{ptt_city[:10]}",
            "layer": "PTT",
            "level": 10,
            "color": "",
            "siteid": generate_ptt_site_id(ptt_city),
            "alias": "",
            "city": ptt_city,
            "uf": ptt_uf,
            "lat": lat_jitter,
            "lon": lon_jitter,
            "type": "PTT"
        })
    
    # 3. Prepare complete city list
    all_cities = []
    for uf, cities_uf in CITIES_UF.items():
        for city in cities_uf:
            all_cities.append((city[0], uf, city[1], city[2]))
    
    # Add PTTs to city list
    for ptt in PTT_DATA:
        if ptt not in all_cities:
            all_cities.append((ptt[0], ptt[1], ptt[2], ptt[3]))
    
    # Group cities by region
    cities_by_region = defaultdict(list)
    for city in all_cities:
        uf = city[1]
        region = get_region(uf, REGIONS)
        cities_by_region[region].append(city)
    
    # Calculate regional proportional distribution
    regional_dist = {}
    total_elements = args.e
    for region, proportion in REGIONAL_PROPORTION.items():
        regional_dist[region] = round(proportion * total_elements)
    
    # Adjust for rounding differences
    diff = total_elements - sum(regional_dist.values())
    if diff != 0:
        largest_region = max(REGIONAL_PROPORTION, key=REGIONAL_PROPORTION.get)
        regional_dist[largest_region] += diff
 
    # 4. Initialize elements list including PTTs
    elements = ptt_elements.copy()

    # Dictionaries for element storage and counters
    site_counters = defaultdict(lambda: defaultdict(int))
    rtics = []
    rtrrs = []
    rtprs = []
    rted_pairs = []
    swacs = []
    
    # Calculate RTIC quantities per region
    rtics_per_region = {}
    total_rtics = actual_dist["RTIC"]
    
    # Initial distribution based on regional proportion
    for region, proportion in REGIONAL_PROPORTION.items():
        rtics_per_region[region] = max(
            1,  # Minimum 1 per region
            round(proportion * total_rtics)
        )
    
    # Adjust difference
    total_rtics_calculated = sum(rtics_per_region.values())
    if total_rtics_calculated < total_rtics:
        # Add extra RTICs in largest regions
        for region in sorted(rtics_per_region, key=rtics_per_region.get, reverse=True):
            if total_rtics_calculated < total_rtics:
                rtics_per_region[region] += 1
                total_rtics_calculated += 1
            else:
                break
    
    # Generate RTICs per region
    for region, qty_rtics_region in rtics_per_region.items():
        # Get mandatory hubs first
        mandatory_hubs = REGIONAL_HIERARCHY[region]["hubs"]
        available_cities = cities_by_region[region].copy()
        
        # Generate mandatory hubs
        generated_hubs = []
        for hub in mandatory_hubs:
            hub_city = next((c for c in available_cities if c[0] == hub), None)
            if hub_city:
                siteid = generate_site_id(
                    hub_city[1], hub_city[0], "RTIC", 
                    site_counters[hub_city[1]+hub_city[0]]["RTIC"] + 1,
                    ABBREVIATIONS
                )
                site_counters[hub_city[1]+hub_city[0]]["RTIC"] += 1
                
                elements.append({
                    "element": f"RTIC-{hub[:3].upper()}{len(rtics)+1:02d}-01",
                    "layer": "INNER-CORE",
                    "level": 1,
                    "color": "",
                    "siteid": siteid,
                    "alias": "",
                    "city": hub_city[0],
                    "uf": hub_city[1],
                    "lat": hub_city[2] + random.uniform(-0.0005, 0.0005),
                    "lon": hub_city[3] + random.uniform(-0.0005, 0.0005),
                    "type": "RTIC"
                })
                rtics.append(elements[-1])
                generated_hubs.append(hub)
                available_cities.remove(hub_city)
        
        # Generate extra RTICs if needed
        extra_rtics = qty_rtics_region - len(generated_hubs)
        if extra_rtics > 0:
            # Prioritize cities with PTTs
            ptt_cities = [c for c in available_cities if c[0] in [p[0] for p in PTT_DATA]]
            if not ptt_cities:
                ptt_cities = available_cities
            
            for _ in range(extra_rtics):
                if not ptt_cities:
                    break
                    
                city = random.choice(ptt_cities)
                siteid = generate_site_id(
                    city[1], city[0], "RTIC", 
                    site_counters[city[1]+city[0]]["RTIC"] + 1,
                    ABBREVIATIONS
                )
                site_counters[city[1]+city[0]]["RTIC"] += 1
                
                elements.append({
                    "element": f"RTIC-{city[0][:3].upper()}{len(rtics)+1:02d}-01",
                    "layer": "INNER-CORE",
                    "level": 1,
                    "color": "",
                    "siteid": siteid,
                    "alias": "",
                    "city": city[0],
                    "uf": city[1],
                    "lat": city[2] + random.uniform(-0.0005, 0.0005),
                    "lon": city[3] + random.uniform(-0.0005, 0.0005),
                    "type": "RTIC"
                })
                rtics.append(elements[-1])
                ptt_cities.remove(city)
                if city in available_cities:
                    available_cities.remove(city)
    
    # Calculate RTRR quantities per region
    rtrrs_per_region = {}
    total_rtrrs = actual_dist["RTRR"]
    
    # Initial distribution based on regional proportion
    for region, proportion in REGIONAL_PROPORTION.items():
        rtrrs_per_region[region] = max(
            1,  # Minimum 1 per region
            round(proportion * total_rtrrs)
        )
    
    # Adjust difference
    total_rtrrs_calculated = sum(rtrrs_per_region.values())
    if total_rtrrs_calculated < total_rtrrs:
        for region in sorted(rtrrs_per_region, key=rtrrs_per_region.get, reverse=True):
            if total_rtrrs_calculated < total_rtrrs:
                rtrrs_per_region[region] += 1
                total_rtrrs_calculated += 1
            else:
                break
    
    # Generate RTRRs per region
    for region, qty_rtrrs_region in rtrrs_per_region.items():
        # Get mandatory sub-regions first
        mandatory_sub_regions = list(REGIONAL_HIERARCHY[region]["sub-regioes"].keys())
        available_cities = cities_by_region[region].copy()
        
        # Generate one RTRR per mandatory sub-region
        generated_subs = []
        for sub_region in mandatory_sub_regions:
            # Select representative city (first UF of the sub-region)
            rep_uf = REGIONAL_HIERARCHY[region]["sub-regioes"][sub_region][0]
            sub_cities = [c for c in available_cities if c[1] == rep_uf]
            
            if sub_cities:
                rep_city = sub_cities[0]
                siteid = generate_site_id(
                    rep_city[1], rep_city[0], "RTRR", 
                    site_counters[rep_city[1]+rep_city[0]]["RTRR"] + 1,
                    ABBREVIATIONS
                )
                site_counters[rep_city[1]+rep_city[0]]["RTRR"] += 1
                
                elements.append({
                    "element": f"RTRR-{sub_region[:5]}{len(rtrrs)+1:02d}-01",
                    "layer": "REFLECTOR",
                    "level": 3,
                    "color": "",
                    "siteid": siteid,
                    "alias": "",
                    "city": rep_city[0],
                    "uf": rep_city[1],
                    "lat": rep_city[2] + random.uniform(-0.0005, 0.0005),
                    "lon": rep_city[3] + random.uniform(-0.0005, 0.0005),
                    "type": "RTRR"
                })
                rtrrs.append(elements[-1])
                generated_subs.append(sub_region)
                if rep_city in available_cities:
                    available_cities.remove(rep_city)
        
        # Generate extra RTRRs if needed
        extra_rtrrs = qty_rtrrs_region - len(generated_subs)
        if extra_rtrrs > 0:
            # Prioritize cities with PTTs
            ptt_cities = [c for c in available_cities if c[0] in [p[0] for p in PTT_DATA]]
            if not ptt_cities:
                ptt_cities = available_cities
            
            for _ in range(extra_rtrrs):
                if not ptt_cities:
                    break
                    
                city = random.choice(ptt_cities)
                siteid = generate_site_id(
                    city[1], city[0], "RTRR", 
                    site_counters[city[1]+city[0]]["RTRR"] + 1,
                    ABBREVIATIONS
                )
                site_counters[city[1]+city[0]]["RTRR"] += 1
                
                elements.append({
                    "element": f"RTRR-{city[0][:5]}{len(rtrrs)+1:02d}-01",
                    "layer": "REFLECTOR",
                    "level": 3,
                    "color": "",
                    "siteid": siteid,
                    "alias": "",
                    "city": city[0],
                    "uf": city[1],
                    "lat": city[2] + random.uniform(-0.0005, 0.0005),
                    "lon": city[3] + random.uniform(-0.0005, 0.0005),
                    "type": "RTRR"
                })
                rtrrs.append(elements[-1])
                ptt_cities.remove(city)
                if city in available_cities:
                    available_cities.remove(city)
    
    # 5. Generate RTPRs (regional proportional distribution)
    for region, qty_region in regional_dist.items():
        qty_rtpr_region = max(1, round(actual_dist["RTPR"] * (qty_region / total_elements)))
        region_cities = cities_by_region[region]
        
        if not region_cities:
            continue
            
        for i in range(qty_rtpr_region):
            # Prioritize cities with PTTs in region
            ptt_cities = [c for c in region_cities if c[0] in [p[0] for p in PTT_DATA]]
            if not ptt_cities:
                city = random.choice(region_cities)
            else:
                city = random.choice(ptt_cities)
            
            siteid = generate_site_id(
                city[1], city[0], "RTPR", 
                site_counters[city[1]+city[0]]["RTPR"] + 1,
                ABBREVIATIONS
            )
            site_counters[city[1]+city[0]]["RTPR"] += 1
            
            elements.append({
                "element": f"RTPR-{city[1]}{i+1:02d}-01",
                "layer": "PEERING",
                "level": 4,
                "color": "",
                "siteid": siteid,
                "alias": "",
                "city": city[0],
                "uf": city[1],
                "lat": city[2] + random.uniform(-0.0005, 0.0005),
                "lon": city[3] + random.uniform(-0.0005, 0.0005),
                "type": "RTPR"
            })
            rtprs.append(elements[-1])
    
    # 6. Generate RTEDs in pairs (regional proportional distribution)
    for region, qty_region in regional_dist.items():
        qty_rted_region = max(2, round(actual_dist["RTED"] * (qty_region / total_elements)))
        # Ensure parity
        if qty_rted_region % 2 != 0:
            qty_rted_region += 1
            
        region_cities = cities_by_region[region]
        
        if not region_cities or qty_rted_region < 2:
            continue
            
        region_pairs = qty_rted_region // 2
        for i in range(region_pairs):
            # Select base city
            base_city = random.choice(region_cities)
            
            # Find nearest city for the pair
            pair_city = min(
                [c for c in region_cities if c != base_city],
                key=lambda c: geographic_distance(
                    base_city[2], base_city[3], c[2], c[3]
                )
            )
            
            # Create first element
            siteid1 = generate_site_id(
                base_city[1], base_city[0], "RTED", 
                site_counters[base_city[1]+base_city[0]]["RTED"] + 1,
                ABBREVIATIONS
            )
            site_counters[base_city[1]+base_city[0]]["RTED"] += 1
            
            elements.append({
                "element": f"RTED-{base_city[1]}{i+1:02d}-01",
                "layer": "EDGE",
                "level": 5,
                "color": "",
                "siteid": siteid1,
                "alias": "",
                "city": base_city[0],
                "uf": base_city[1],
                "lat": base_city[2] + random.uniform(-0.0005, 0.0005),
                "lon": base_city[3] + random.uniform(-0.0005, 0.0005),
                "type": "RTED"
            })
            rted1 = elements[-1]
            
            # Create second element
            siteid2 = generate_site_id(
                pair_city[1], pair_city[0], "RTED", 
                site_counters[pair_city[1]+pair_city[0]]["RTED"] + 1,
                ABBREVIATIONS
            )
            site_counters[pair_city[1]+pair_city[0]]["RTED"] += 1
            
            elements.append({
                "element": f"RTED-{pair_city[1]}{i+1:02d}-02",
                "layer": "EDGE",
                "level": 5,
                "color": "",
                "siteid": siteid2,
                "alias": "",
                "city": pair_city[0],
                "uf": pair_city[1],
                "lat": pair_city[2] + random.uniform(-0.0005, 0.0005),
                "lon": pair_city[3] + random.uniform(-0.0005, 0.0005),
                "type": "RTED"
            })
            rted2 = elements[-1]
            
            rted_pairs.append((rted1, rted2))
    
    # 7. Generate SWACs (regional proportional distribution)
    for region, qty_region in regional_dist.items():
        qty_swac_region = round(actual_dist["SWAC"] * (qty_region / total_elements))
        region_cities = cities_by_region[region]
        
        if not region_cities:
            continue
            
        for i in range(qty_swac_region):
            city = random.choice(region_cities)
            siteid = generate_site_id(
                city[1], city[0], "SWAC", 
                site_counters[city[1]+city[0]]["SWAC"] + 1,
                ABBREVIATIONS
            )
            site_counters[city[1]+city[0]]["SWAC"] += 1
            
            elements.append({
                "element": f"SWAC-{city[1]}{i+1:02d}-01",
                "layer": "METRO",
                "level": 8,
                "color": "",
                "siteid": siteid,
                "alias": "",
                "city": city[0],
                "uf": city[1],
                "lat": city[2] + random.uniform(-0.0005, 0.0005),
                "lon": city[3] + random.uniform(-0.0005, 0.0005),
                "type": "SWAC"
            })
            swacs.append(elements[-1])
    
    # 8. Generate connections
    connections = []
    
    # Group RTICs by region
    rtics_by_region = defaultdict(list)
    for rtic in rtics:
        region = get_region(rtic["uf"], REGIONS)
        rtics_by_region[region].append(rtic)

    # Regional rings
    for region, region_rtics in rtics_by_region.items():
        n = len(region_rtics)
        if n < 2:
            continue
            
        for i in range(n):
            j = (i+1) % n
            connections.append({
                "endpoint-a": region_rtics[i]["element"],
                "endpoint-b": region_rtics[j]["element"],
                "connection_text": f"Core Ring {region}",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })

    # Strategic region order
    region_order = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    main_hubs = []
    for region in region_order:
        if rtics_by_region.get(region):
            main_hubs.append(rtics_by_region[region][0])

    # National ring
    n_national = len(main_hubs)
    if n_national >= 2:
        for i in range(n_national):
            j = (i+1) % n_national
            connections.append({
                "endpoint-a": main_hubs[i]["element"],
                "endpoint-b": main_hubs[j]["element"],
                "connection_text": "National Ring",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })

    # Cross-region redundancy
    for i in range(len(region_order)):
        region_curr = region_order[i]
        region_next = region_order[(i+1) % len(region_order)]
        
        if (len(rtics_by_region.get(region_curr, [])) >= 2 and 
           rtics_by_region.get(region_next)):
            
            second_hub = rtics_by_region[region_curr][1]
            next_hub = rtics_by_region[region_next][0]
            
            connections.append({
                "endpoint-a": second_hub["element"],
                "endpoint-b": next_hub["element"],
                "connection_text": "Cross-Region Redundancy",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
    
    # RTRR to RTIC connections (2 per RTRR)
    for rtrr in rtrrs:
        rtrr_region = get_region(rtrr["uf"], REGIONS)
        region_rtics = [r for r in rtics if get_region(r["uf"], REGIONS) == rtrr_region]
        if len(region_rtics) < 2:
            sorted_rtics = sorted(
                rtics,
                key=lambda r: geographic_distance(rtrr["lat"], rtrr["lon"], r["lat"], r["lon"])
            )[:2]
        else:
            sorted_rtics = region_rtics[:2]
        
        for rtic in sorted_rtics:
            connections.append({
                "endpoint-a": rtrr["element"],
                "endpoint-b": rtic["element"],
                "connection_text": "Reflector Link",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
    
    # RTPR to RTIC connections (2 per RTPR)
    for rtpr in rtprs:
        sorted_rtics = sorted(
            rtics,
            key=lambda r: geographic_distance(rtpr["lat"], rtpr["lon"], r["lat"], r["lon"])
        )[:2]
        
        for rtic in sorted_rtics:
            connections.append({
                "endpoint-a": rtpr["element"],
                "endpoint-b": rtic["element"],
                "connection_text": "Peering Link",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
    
    # RTED connections (pairs and to RTICs)
    for pair in rted_pairs:
        connections.append({
            "endpoint-a": pair[0]["element"],
            "endpoint-b": pair[1]["element"],
            "connection_text": "Edge Pair",
            "strokeWidth": "",
            "strokeColor": "",
            "dashed": "",
            "fontStyle": "",
            "fontSize": ""
        })
        
        sorted_rtics1 = sorted(
            rtics,
            key=lambda r: geographic_distance(pair[0]["lat"], pair[0]["lon"], r["lat"], r["lon"])
        )
        
        rtic1 = sorted_rtics1[0]
        connections.append({
            "endpoint-a": pair[0]["element"],
            "endpoint-b": rtic1["element"],
            "connection_text": "Edge to Core",
            "strokeWidth": "",
            "strokeColor": "",
            "dashed": "",
            "fontStyle": "",
            "fontSize": ""
        })
        
        sorted_rtics2 = sorted(
            [r for r in rtics if r != rtic1],
            key=lambda r: geographic_distance(pair[1]["lat"], pair[1]["lon"], r["lat"], r["lon"])
        )
        
        rtic2 = sorted_rtics2[0] if sorted_rtics2 else sorted_rtics1[0]
        
        connections.append({
            "endpoint-a": pair[1]["element"],
            "endpoint-b": rtic2["element"],
            "connection_text": "Edge to Core",
            "strokeWidth": "",
            "strokeColor": "",
            "dashed": "",
            "fontStyle": "",
            "fontSize": ""
        })
    
    # SWAC connections (rings to RTED pairs)
    swacs_by_city = defaultdict(list)
    for swac in swacs:
        key = f"{swac['uf']}-{swac['city']}"
        swacs_by_city[key].append(swac)
    
    for city_swacs in swacs_by_city.values():
        random.shuffle(city_swacs)
        
        # Connect in ring (only if more than one element)
        if len(city_swacs) > 1:
            for i in range(len(city_swacs)):
                nxt = (i + 1) % len(city_swacs)
                connections.append({
                    "endpoint-a": city_swacs[i]["element"],
                    "endpoint-b": city_swacs[nxt]["element"],
                    "connection_text": "Metro Ring",
                    "strokeWidth": "",
                    "strokeColor": "",
                    "dashed": "",
                    "fontStyle": "",
                    "fontSize": ""
                })
        
        # Connect ends to nearest RTED pair
        if len(city_swacs) > 0 and rted_pairs:
            ref_city = (city_swacs[0]["lat"], city_swacs[0]["lon"])
            rted_pair = min(
                rted_pairs,
                key=lambda p: min(
                    geographic_distance(ref_city[0], ref_city[1], p[0]["lat"], p[0]["lon"]),
                    geographic_distance(ref_city[0], ref_city[1], p[1]["lat"], p[1]["lon"])
                )
            )
            
            connections.append({
                "endpoint-a": city_swacs[0]["element"],
                "endpoint-b": rted_pair[0]["element"],
                "connection_text": "Metro to Edge",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
            
            connections.append({
                "endpoint-a": city_swacs[-1]["element"],
                "endpoint-b": rted_pair[1]["element"],
                "connection_text": "Metro to Edge",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
    
    # 9. Output generation
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_dir = f"TOPOLOGY_{args.e}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Write elements.csv
    with open(f"{output_dir}/elements.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=["element", "layer", "level", "color", "siteid", "alias"],
            delimiter=";"
        )
        writer.writeheader()
        for elem in elements:
            writer.writerow({
                "element": remove_accents(elem["element"]),
                "layer": remove_accents(elem["layer"]),
                "level": elem["level"],
                "color": remove_accents(elem["color"]),
                "siteid": remove_accents(elem["siteid"]),
                "alias": remove_accents(elem["alias"])
            })
    
    # Write connections.csv
    with open(f"{output_dir}/connections.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=["endpoint-a", "endpoint-b", "connection_text", 
                       "strokeWidth", "strokeColor", "dashed", 
                       "fontStyle", "fontSize"],
            delimiter=";"
        )
        writer.writeheader()
        for conn in connections:
            writer.writerow({
                "endpoint-a": remove_accents(conn["endpoint-a"]),
                "endpoint-b": remove_accents(conn["endpoint-b"]),
                "connection_text": remove_accents(conn["connection_text"]),
                "strokeWidth": remove_accents(conn["strokeWidth"]),
                "strokeColor": remove_accents(conn["strokeColor"]),
                "dashed": remove_accents(conn["dashed"]),
                "fontStyle": remove_accents(conn["fontStyle"]),
                "fontSize": remove_accents(conn["fontSize"])
            })
    
    # Write locations.csv
    with open(f"{output_dir}/locations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=["siteid", "Location", "GeographicRegion", "Latitude", "Longitude"],
            delimiter=";"
        )
        writer.writeheader()
        for elem in elements:
            region = get_region(elem["uf"], REGIONS)
            writer.writerow({
                "siteid": remove_accents(elem["siteid"]),
                "Location": remove_accents(elem["city"]),
                "GeographicRegion": remove_accents(region),
                "Latitude": decimal_to_dms(elem["lat"], "lat"),
                "Longitude": decimal_to_dms(elem["lon"], "lon")
            })
    
    # Generate Summary
    summary = f"""
GENERATED TOPOLOGY SUMMARY
==========================

Generation date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total elements: {args.e}
Configuration file: {args.c}

DISTRIBUTION BY LAYER:
----------------------
INNER-CORE (RTIC): {actual_dist["RTIC"]} elements
REFLECTOR (RTRR): {actual_dist["RTRR"]} elements
PEERING (RTPR): {actual_dist["RTPR"]} elements
EDGE (RTED): {actual_dist["RTED"]} elements
METRO (SWAC): {actual_dist["SWAC"]} elements

GEOGRAPHIC DISTRIBUTION:
------------------------
Regions:
"""
    
    region_counts = defaultdict(int)
    for elem in elements:
        region = get_region(elem["uf"], REGIONS)
        region_counts[region] += 1
    
    for region, count in region_counts.items():
        summary += f"  {region}: {count} elements\n"
    
    summary += "\nStates (UF) with most elements:\n"
    uf_counts = defaultdict(int)
    for elem in elements:
        uf_counts[elem["uf"]] += 1
    
    for uf, count in sorted(uf_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        summary += f"  {uf}: {count} elements\n"
    
    summary += f"""
GENERATED CONNECTIONS:
----------------------
Total connections: {len(connections)}
Types (approximate):
  INNER-CORE (Rings + Redundancy): {len([c for c in connections if 'Ring' in c['connection_text'] or 'Redundancy' in c['connection_text']])}
  REFLECTOR to CORE: {len([c for c in connections if 'Reflector' in c['connection_text']])}
  PEERING to CORE: {len([c for c in connections if 'Peering' in c['connection_text']])}
  EDGE (Pairs + to CORE): {len([c for c in connections if 'Edge' in c['connection_text']])}
  METRO (Rings + to EDGE): {len([c for c in connections if 'Metro' in c['connection_text']])}

GENERATED FILES:
----------------
1. elements.csv: {len(elements)} records
2. connections.csv: {len(connections)} records
3. locations.csv: {len(elements)} records

Output directory: {output_dir}

🔗 Repository - Follow on GitHub for new versions and updates

Generate topologies dynamically
https://github.com/flashbsb/network-topology-generator

Execute massive commands simply and generate connection information between network elements
https://github.com/flashbsb/network-data-extractor

Dimension backbone topologies for testing:
https://github.com/flashbsb/backbone-network-topology-generator
"""
    
    with open(f"{output_dir}/summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)
    
    print(f"Topology successfully generated in folder: {output_dir}")
    print(summary)

if __name__ == "__main__":
    main()
