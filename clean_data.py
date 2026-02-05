
import pandas as pd
import numpy as np
import os

# Paths
DATA_DIR = r"C:\Users\nithi\OneDrive\Desktop\dataverse\VelocityMart"
SKU_PATH = os.path.join(DATA_DIR, "sku_master.csv")
ORDER_PATH = os.path.join(DATA_DIR, "order_history.csv")
PICKER_PATH = os.path.join(DATA_DIR, "picker_movement.csv")
CONSTRAINTS_PATH = os.path.join(DATA_DIR, "warehouse_constraints.csv")

OUTPUT_DIR = os.path.join(DATA_DIR, "cleaned_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_data():
    print("Loading datasets...")
    sku_df = pd.read_csv(SKU_PATH)
    # Load constraints with explicit string type for IDs
    constraints_df = pd.read_csv(CONSTRAINTS_PATH, dtype={'slot_id': str})
    picker_df = pd.read_csv(PICKER_PATH)
    order_df = pd.read_csv(ORDER_PATH)
    return sku_df, order_df, picker_df, constraints_df

def fix_decimal_drift(sku_df):
    print("\n--- DETECTING DECIMAL DRIFT ---")
    # Hypothesis: Items > 80kg are likely errors (10x).
    drift_mask = sku_df['weight_kg'] > 80.0
    affected_count = drift_mask.sum()
    print(f"Detected {affected_count} SKUs with potential decimal drift (Weight > 80kg).")
    
    if affected_count > 0:
        # Correction
        sku_df.loc[drift_mask, 'weight_kg'] = sku_df.loc[drift_mask, 'weight_kg'] / 10.0
        print("Correction applied: Divided weights by 10.")
    
    return sku_df

def detect_ghost_inventory(sku_df, constraints_df):
    print("\n--- DETECTING GHOST INVENTORY ---")
    valid_slots = set(constraints_df['slot_id'].astype(str).str.strip())
    sku_slots = sku_df['current_slot'].astype(str).str.strip()
    
    # Check if current_slot exists in valid_slots
    mask_ghost = ~sku_slots.isin(valid_slots) & sku_slots.replace('nan', np.nan).notna()
    ghost_count = mask_ghost.sum()
    
    print(f"Detected {ghost_count} SKUs assigned to non-existent slots (Ghost Inventory).")
    
    if ghost_count > 0:
        print("Sample ghost inventory:")
        print(sku_df[mask_ghost][['sku_id', 'current_slot']].head())
        # Action: Set to NaN
        sku_df.loc[mask_ghost, 'current_slot'] = np.nan
        print("Correction applied: Set invalid slots to NaN.")
        
    return sku_df

def clean_picker_movement(picker_df):
    print("\n--- DATA FORENSICS: PICKER MOVEMENT ---")
    
    picker_df['movement_timestamp'] = pd.to_datetime(picker_df['movement_timestamp'])
    
    # Sort by Picker and Time
    picker_df = picker_df.sort_values(by=['picker_id', 'movement_timestamp'])
    
    # Calculate time diff between pics
    picker_df['prev_time'] = picker_df.groupby('picker_id')['movement_timestamp'].shift(1)
    picker_df['time_diff'] = (picker_df['movement_timestamp'] - picker_df['prev_time']).dt.total_seconds()
    
    # If time_diff is very large (e.g. > 1 hour), it's a new shift. 
    # If time_diff is NaN (first pick), we can't calc speed based on prev.
    # We can try to use order_timestamp as a fallback for first pick? No, order time is misleading.
    # However, the dataset has 'travel_distance_m'. This implies distance *traveled* for this pick.
    # So 'time_diff' is roughly the travel time? 
    # Or is 'travel_distance_m' the distance from the PREVIOUS pick?
    # Yes, usually "travel distance" is from Last Pos to Curr Pos.
    
    # Filter valid intervals (e.g. < 30 mins)
    valid_interval = (picker_df['time_diff'] > 0) & (picker_df['time_diff'] < 1800)
    
    picker_df['calculated_speed'] = np.nan
    picker_df.loc[valid_interval, 'calculated_speed'] = \
        picker_df.loc[valid_interval, 'travel_distance_m'] / picker_df.loc[valid_interval, 'time_diff']

    # Detect Shortcuts: Impossibly high speed
    # Threshold: 3 m/s (approx 10.8 km/h) is very fast for warehouse picking (stop & go).
    # 5 m/s is definitely impossible walking.
    submission_threshold = 4.0 
    
    shortcut_mask = picker_df['calculated_speed'] > submission_threshold
    shortcut_count = shortcut_mask.sum()
    
    print(f"Detected {shortcut_count} movements with suspicious speed (> {submission_threshold} m/s).")
    
    if shortcut_count > 0:
        print("Sample suspicious movements:")
        print(picker_df[shortcut_mask][['picker_id', 'travel_distance_m', 'time_diff', 'calculated_speed']].head())
        picker_df['is_suspicious'] = shortcut_mask
    else:
        picker_df['is_suspicious'] = False

    return picker_df

def main():
    sku_df, order_df, picker_df, constraints_df = load_data()
    
    # 1. Fix Sku Master
    sku_df_clean = fix_decimal_drift(sku_df)
    sku_df_clean = detect_ghost_inventory(sku_df_clean, constraints_df)
    
    # 2. Clean Picker Movement
    picker_df_clean = clean_picker_movement(picker_df)
    
    # 3. Save Cleaned Data
    print("\nSaving cleaned datasets to", OUTPUT_DIR)
    sku_df_clean.to_csv(os.path.join(OUTPUT_DIR, "sku_master_cleaned.csv"), index=False)
    # Drop temp columns for clean output
    picker_out = picker_df_clean.drop(columns=['prev_time', 'time_diff', 'calculated_speed'])
    picker_out.to_csv(os.path.join(OUTPUT_DIR, "picker_movement_cleaned.csv"), index=False)
    
    order_df.to_csv(os.path.join(OUTPUT_DIR, "order_history_cleaned.csv"), index=False)
    constraints_df.to_csv(os.path.join(OUTPUT_DIR, "warehouse_constraints_cleaned.csv"), index=False)
    
    print("Forensics complete.")

if __name__ == "__main__":
    main()
