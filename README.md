# 🌐 Backbone Network Topology Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)

Tool for automated generation of hierarchical backbone network topologies, producing laboratory-ready datasets for visualization in tools like Draw.io.

## 🔍 Overview

Generates three essential files for network modeling:
- `elements.csv`: Equipment and attributes
- `connections.csv`: Interconnections between devices
- `locations.csv`: Geographic data (DMS coordinates)

## ⚙️ Installation

### Linux (Debian/Ubuntu)
```bash
sudo apt update && sudo apt install python3 -y
```

### Windows
1. Open Microsoft Store.
2. Search for "Python 3.12+".
3. Click Install.

## 🚀 How to Use

**Basic command:**
```bash
python backbone-network-topology-generator.py -e 300
```

**Options:**
| Argument | Description               | Default      |
|----------|---------------------------|--------------|
| `-e`     | Total elements (30-1000)  | 300          |
| `-c`     | Configuration file path   | config.json  |

**Examples:**
```bash
# Default topology (300 elements)
python backbone-network-topology-generator.py

# Custom topology (500 elements)
python backbone-network-topology-generator.py -e 500 -c my_config.json
```

### Generated Output
A folder named `TOPOLOGY_[QTY]_[TIMESTAMP]` containing:
```
📁 TOPOLOGY_300_20250702120000/
├── 📄 elements.csv    # Equipment and attributes
├── 📄 connections.csv # Interconnections
├── 📄 locations.csv   # Geographic coordinates
└── 📄 summary.txt     # Topology statistics
```

## 🏗️ Element Distribution
(Adjust `config.json` as needed)

### 5-Layer Hierarchy
| Layer          | Element | Proportion | Primary Function               |
|----------------|----------|-----------|--------------------------------|
| Inner-Core     | RTIC     | 2%        | High-capacity core             |
| Reflector      | RTRR     | 3%        | Regional aggregation           |
| Peering        | RTPR     | 3%        | Connection with IXPs           |
| Edge           | RTED     | 12%       | Network edge                   |
| Metro          | SWAC     | 80%       | Metropolitan access            |

### Geographic Regions
| Region         | Proportion 
|----------------|-----------
| Southeast      | 43.2%
| Northeast      | 28.9%
| South          | 12%
| North          | 8.3%
| Central-West   | 7.6%

## 📊 Output Example (summary.txt)
```
GENERATED TOPOLOGY SUMMARY
==========================
Total elements: 300
Total connections: 475

DISTRIBUTION:
------------
RTIC (Inner-Core): 11
RTRR (Reflector): 12
RTPR (Peering): 9
RTED (Edge): 36
SWAC (Metro): 232
```

## 🛠️ What This Project Is Not
- A visual diagram generator (use [Network-Topology-Generator-for-Drawio](https://github.com/flashbsb/Network-Topology-Generator-for-Drawio) for that).
- A network performance simulator.
- A capacity planning tool.

## 📂 CSV Structure

### elements.csv
`element;layer;level;color;siteid;alias`

### connections.csv
`endpoint-a;endpoint-b;connection_text;strokeWidth;strokeColor;dashed;fontStyle;fontSize`

### locations.csv
`siteid;Location;GeographicRegion;Latitude;Longitude`

## 🔗 Repository - Follow on GitHub for new versions and updates

**Generate topologies dynamically**
https://github.com/flashbsb/network-topology-generator

**Execute massive commands simply and generate connection information between network elements**
https://github.com/flashbsb/network-data-extractor

**Dimension backbone topologies for testing:**
https://github.com/flashbsb/backbone-network-topology-generator

## 📜 License:
[MIT License](LICENSE)
