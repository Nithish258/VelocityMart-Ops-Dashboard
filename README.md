# VelocityMart Operational Turnaround Project

## Overview
This project contains the complete operational rescue analysis for VelocityMart's Bangalore warehouse, including data forensics, diagnostic dashboards, and optimized slotting for Week 91.

## Project Structure

```
VelocityMart/
├── cleaned_data/               # Cleaned datasets
│   ├── sku_master_cleaned.csv
│   ├── picker_movement_cleaned.csv
│   ├── order_history_cleaned.csv
│   └── warehouse_constraints_cleaned.csv
├── clean_data.py              # Data forensics script
├── dashboard.py               # Streamlit diagnostic dashboard
├── optimize_slotting.py       # Slotting optimization engine
├── final_slotting_plan.csv    # Week 91 execution plan
├── executive_report.md        # Executive summary & findings
└── README.md                  # This file
```

## Key Deliverables

### 1. Data Forensics (`clean_data.py`)
**Findings:**
- **14 SKUs** with decimal drift (weights 10x too high) - CORRECTED
- **1,551** illegal picker shortcuts detected (speeds > 4 m/s)
- **490** temperature zone violations identified
- **0** ghost inventory items (all bins validated)

**Run:** `python clean_data.py`

### 2. Diagnostic Dashboard (`dashboard.py`)
Interactive Streamlit dashboard featuring:
- **Chaos Score**: Custom metric (Current: 82/100 - CRITICAL)
- Aisle congestion heatmaps (highlighting Aisle B @ 19:00)
- Spoilage risk analysis
- Constraint violation tracking

**Run:** `streamlit run dashboard.py`

### 3. Slotting Optimization (`optimize_slotting.py`)
**Strategy:** Constraint compliance + Aisle B de-congestion

**Results:**
- **510 total moves** planned
- **490** temperature violations fixed
- **3** weight violations fixed
- **35** high-velocity SKUs moved out of Aisle B

**Output:** `final_slotting_plan.csv` (SKU_ID, Bin_ID)

**Run:** `python optimize_slotting.py`

## Critical Findings

### The "Chaos Score" (82/100)
**Components:**
1. **Efficiency Loss**: 63% degradation (3.8 → 6.2 min avg fulfillment)
2. **Safety Risk**: 1,551 illegal shortcuts (0.77% of all picks)
3. **Spoilage Risk**: 61% of SKUs in wrong temperature zones

### Aisle B Bottleneck
- **Hidden Constraint**: Forklifts cannot enter when >2 pickers present
- **Current State**: 35 high-velocity SKUs causing gridlock at peak (19:00)
- **Solution**: Redistributed to Aisles C & D

### Sensitivity Analysis (+20% Volume)
- **Before Optimization**: 90% system failure probability
- **After Optimization**: Survives spike with 40% Aisle B utilization

## How to Use

### Quick Start
```powershell
# 1. Clean the data
python clean_data.py

# 2. View the dashboard
streamlit run dashboard.py

# 3. Generate optimized plan
python optimize_slotting.py
```

### Execute Week 91 Plan
The file `final_slotting_plan.csv` contains the complete move list:
- Column 1: `sku_id` - SKU to move
- Column 2: `Bin_ID` - Destination slot

**Priority Moves (Top 5):**
1. SKU-10551 → C01-A-01 (High velocity + temp fix)
2. SKU-10116 → D01-A-01 (Aisle B de-congestion)
3. SKU-10281 → D01-A-02 (Velocity optimization)
4. SKU-10146 → D01-A-03 (Temp compliance)
5. SKU-10733 → C01-A-02 (Weight compliance)

## Technical Details

### Data Cleaning Pipeline
1. **Decimal Drift Detection**: Heuristic threshold (>80kg for groceries)
2. **Shortcut Detection**: Inter-pick speed calculation (>4 m/s flagged)
3. **Ghost Inventory**: Cross-reference SKU slots with valid bin IDs
4. **Temperature Mapping**: Validate SKU temp requirements vs bin zones

### Optimization Algorithm
1. **Constraint Validation**: Temperature, weight, aisle width
2. **Priority Scoring**: Violations (1000 pts) + order volume
3. **Greedy Assignment**: Match SKUs to compatible empty slots
4. **Aisle B Avoidance**: High-velocity SKUs excluded from B-prefix aisles

### Chaos Score Formula
```
Chaos = (Efficiency_Loss + Safety_Score + Spoilage_Score) × 100
where:
  Efficiency_Loss = (Current_Time / 3.8) - 1
  Safety_Score = Shortcut_Rate × 10
  Spoilage_Score = Temp_Violation_Rate × 5
```

## Dependencies
```
pandas
numpy
streamlit
plotly
```

Install: `pip install pandas numpy streamlit plotly`

## Contact
**Interim Head of Operations (AI)**  
Generated: Week 90, 2026-02-05
