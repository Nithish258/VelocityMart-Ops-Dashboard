
import pandas as pd
import numpy as np
import os

# Paths
DATA_DIR = r"C:\Users\nithi\OneDrive\Desktop\dataverse\VelocityMart\cleaned_data"
OUTPUT_FILE = r"C:\Users\nithi\OneDrive\Desktop\dataverse\VelocityMart\final_slotting_plan.csv"

def load_data():
    sku_df = pd.read_csv(os.path.join(DATA_DIR, "sku_master_cleaned.csv"))
    constraints_df = pd.read_csv(os.path.join(DATA_DIR, "warehouse_constraints_cleaned.csv"), dtype={'slot_id': str})
    order_df = pd.read_csv(os.path.join(DATA_DIR, "order_history_cleaned.csv"))
    # Clean slot IDs in SKU if not done
    sku_df['current_slot'] = sku_df['current_slot'].astype(str).str.strip()
    constraints_df['slot_id'] = constraints_df['slot_id'].astype(str).str.strip()
    return sku_df, constraints_df, order_df

def optimize():
    sku_df, constraints_df, order_df = load_data()
    
    print(f"Total SKUs: {len(sku_df)}")
    print(f"Total Slots: {len(constraints_df)}")
    
    # 1. Identify High Velocity SKUs
    # Count orders per SKU
    sku_counts = order_df['sku_id'].value_counts()
    # Top 50 or Top 10%?
    # "Identify the top 50 SKUs to move immediately"
    # Let's consider High Velocity as Top 100 for checking congestion.
    high_velocity_skus = set(sku_counts.head(200).index)
    
    sku_df['is_high_velocity'] = sku_df['sku_id'].isin(high_velocity_skus)
    sku_df['order_count'] = sku_df['sku_id'].map(sku_counts).fillna(0)
    
    # 2. Merge Constraints to current slots
    current_state = sku_df.merge(constraints_df, left_on='current_slot', right_on='slot_id', how='left')
    
    # 3. Identify Violations
    # Temp Mismatch
    # Handle NaN in temp_zone (maybe ambient?) - Assuming constraints are complete.
    temp_violation = (current_state['temp_req'] != current_state['temp_zone']) & current_state['temp_zone'].notna()
    
    # Weight Mismatch
    weight_violation = (current_state['weight_kg'] > current_state['max_weight_kg'])
    
    # Aisle B Congestion (High Velocity in Aisle B - Assume A02 is Aisle B?)
    # "Forklifts cannot enter Aisle B..."
    # We inferred Aisle B is 'A02' or explicitly 'B'? 
    # Let's check Aisle IDs. constraints_df['aisle_id'].
    # If aisle_id is like 'A02', we need tomap 'Aisle B'. 
    # Sample showed 'A01-A-01'. Aisle ID 'A01'. 
    # Maybe 'B' is 'Aisle B' literally? Or 'Bxx'?
    # Let's assume Aisle IDs are 'A01', 'B01', 'C01' etc?
    # Or maybe 'Aisle B' refers to a specific zone? 
    # Let's look for 'B' in aisle_id.
    # We will assume any aisle starting with 'B' or containing 'B' is target.
    # Or maybe it's the second aisle?
    # Let's wait for script output to see aisle examples.
    # For now, I'll penalize High Velocity on any aisle ID containing 'B'.
    
    # Actually, let's just dump aisle IDs first to be safe. 
    # But I can't interact.
    # I'll add logic: If aisle_id starts with 'B', it's Aisle B.
    
    current_state['aisle_prefix'] = current_state['current_slot'].str.split('-').str[0].str[0] # 'A', 'B', 'C' from 'A01...'?
    # Wait, sample was 'A01-A-01'. 
    # 'aisle_id' column exists. 'A01'.
    # If aisle_id contains 'B', e.g., 'B01', 'B02'.
    
    is_aisle_b = current_state['aisle_id'].astype(str).str.startswith('B')
    congestion_risk = (current_state['is_high_velocity']) & (is_aisle_b)
    
    # Priority for Moving
    # 1. Temp Violations (Critical)
    # 2. Weight Violations (Critical)
    # 3. Congestion Risk (High Impact)
    
    to_move_mask = temp_violation | weight_violation | congestion_risk
    to_move_skus = current_state[to_move_mask].copy()
    
    print(f"Found {len(to_move_skus)} SKUs to move.")
    print(f" - Temp Violations: {temp_violation.sum()}")
    print(f" - Weight Violations: {weight_violation.sum()}")
    print(f" - Aisle B Congestion: {congestion_risk.sum()}")
    
    # Sort by 'Chaos Contribution'? 
    # Violations first, then Order Volume.
    to_move_skus['priority'] = 0
    to_move_skus.loc[temp_violation, 'priority'] += 1000
    to_move_skus.loc[weight_violation, 'priority'] += 1000
    to_move_skus.loc[congestion_risk, 'priority'] += to_move_skus.loc[congestion_risk, 'order_count']
    
    to_move_skus = to_move_skus.sort_values('priority', ascending=False)
    
    # Limit moves? "Optimize under a limited labor budget".
    # Let's try to move all violations + top congestion risks.
    # If too many, maybe cap at 100 moves?
    # Prompt asks for "Identify top 50 SKUs to move". 
    # We can output a plan for all violations (must fix) + top optimization.
    
    # Strategy: Find destinations
    # Set of occupied slots
    occupied_slots = set(sku_df['current_slot'])
    
    # Available slots (All - Occupied)
    all_slots = set(constraints_df['slot_id'])
    empty_slots = list(all_slots - occupied_slots)
    # Build DF for empty slots
    empty_slots_df = constraints_df[constraints_df['slot_id'].isin(empty_slots)].copy()
    
    # Optimization Loop
    moves = []
    
    # Track used slots (start with occupied, remove source when moving? No, we plan moves sequentially)
    # Ideally, we move SKU A to Empty Slot E. E is now occupied. Old Slot of A is now Empty.
    # This allows chaining.
    
    # Current state of slots: Map SlotID -> SKU_ID (or None)
    slot_map = dict(zip(sku_df['current_slot'], sku_df['sku_id']))
    
    # We want to change the mapping for 'to_move_skus'.
    
    moved_count = 0
    
    for idx, row in to_move_skus.iterrows():
        sku_id = row['sku_id']
        current_slot = row['current_slot']
        
        # Requirements
        req_temp = row['temp_req']
        weight = row['weight_kg']
        avoid_aisle_b = row['is_high_velocity'] # If high velocity, avoid B.
        
        # find candidate in empty_slots_df
        # Filter dataframe?
        # Aisle B check:
        # We need an 'aisle' column in empty_slots_df calculation if not processed per row.
        # Let's pre-calculate 'is_aisle_b' for empty_slots_df
        
        # Find valid candidates
        # 1. Temp match
        candidates = empty_slots_df[empty_slots_df['temp_zone'] == req_temp]
        # 2. Weight limit
        candidates = candidates[candidates['max_weight_kg'] >= weight]
        # 3. Avoid Aisle B if high velocity
        if avoid_aisle_b:
             candidates = candidates[~candidates['aisle_id'].str.startswith('B')]
        
        if candidates.empty:
             # Try Swap? (Too complex for this script? Maybe just log failure)
             # Or relax Aisle B constraint if it helps? 
             # If violation (Temp/Weight), we MUST move even to Aisle B? 
             # But if High Vel, Aisle B is bad.
             # Let's try relaxing Aisle B constraint for violations.
             if row['priority'] >= 1000:
                  candidates = empty_slots_df[empty_slots_df['temp_zone'] == req_temp]
                  candidates = candidates[candidates['max_weight_kg'] >= weight]
        
        if not candidates.empty:
            # Pick first (or best?)
            # Heuristic: Pick front of aisle? (Shelf A?)
            # Sort keys?
            best_slot = candidates.iloc[0]['slot_id']
            
            # Record Move
            moves.append({'sku_id': sku_id, 'new_slot': best_slot})
            
            # Update State
            # Only delete if this SKU is the one mapped (handle multi-sku in one slot issues safely)
            if current_slot in slot_map and slot_map[current_slot] == sku_id:
                del slot_map[current_slot]
            elif current_slot in slot_map:
                 # Slot occupied by another SKU? Leave it alone, just move this one.
                 pass
            
            slot_map[best_slot] = sku_id
            
            # Remove from empty_slots_df
            # (Inefficient to drop row every time, we can manage detailed list, but DF for simplicity)
            empty_slots_df = empty_slots_df[empty_slots_df['slot_id'] != best_slot]
            
            # Add old slot to empty?
            # We need to get details of old slot to add it back to empty_slots_df.
            # We can lookup row in constraints_df
            old_slot_data = constraints_df[constraints_df['slot_id'] == current_slot]
            if not old_slot_data.empty:
                 empty_slots_df = pd.concat([empty_slots_df, old_slot_data])
            
            moved_count += 1
        else:
            print(f"Could not find slot for {sku_id} (Temp: {req_temp}, W: {weight})")
            # If critical violation, this is bad.
    
    print(f"Planned {moved_count} moves.")
    
    # Generate Full Plan
    # Format: SKU_ID, Bin_ID
    # Based on 'slot_map' which represents final state?
    # Wait, slot_map is Slot -> SKU. We need SKU -> Slot.
    
    final_sku_slot = []
    # Currently slot_map has all SLOTTED skus.
    # What about unslotted?
    # We should iterate all SKUs.
    
    # Invert map
    sku_to_slot = {v: k for k, v in slot_map.items()}
    
    # Original DF
    final_plan = sku_df[['sku_id']].copy()
    final_plan['Bin_ID'] = final_plan['sku_id'].map(sku_to_slot)
    
    # Fill NaN? (Unslotted remains unslotted?)
    # "Respect all hard constraints...".
    # "Generate... exactly two columns".
    
    # Save
    final_plan.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved optimization plan to {OUTPUT_FILE}")
    
    # OUTPUT METRICS FOR REPORT
    print("\n--- METRICS FOR REPORT ---")
    print(f"Chaos Score Inputs:")
    # Recalculate basic stats
    print(f"Total High Velocity SKUs: {len(high_velocity_skus)}")
    print(f"Moves Planned: {moved_count}")
    print(f"Top 5 Moves:")
    for m in moves[:5]:
        print(m)

if __name__ == "__main__":
    optimize()
