#!/usr/bin/env python3
"""
Extract RMSE values from m3ed_results directory and generate CSV.
"""

import os
import re
import glob
import pandas as pd
import numpy as np

def parse_results_file(filepath):
    """Parse a results.txt file and extract RMSE values."""
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find all RMSE values
    rmse_matches = re.findall(r'rmse\s+([\d.]+)', content, re.IGNORECASE)
    rmse_values = [float(r) for r in rmse_matches]
    
    if not rmse_values:
        return None
    
    return rmse_values

def scan_results(base_dir='/media/SSD/m3ed_results'):
    """Scan all result directories and collect data."""
    results = []
    
    dirs = sorted(glob.glob(os.path.join(base_dir, 'spot_*')))
    
    for dirpath in dirs:
        dirname = os.path.basename(dirpath)
        results_file = os.path.join(dirpath, 'results.txt')
        
        rmse_values = parse_results_file(results_file)
        if rmse_values:
            row = {
                'name': dirname,
                'num_runs': len(rmse_values),
                'rmse_mean': np.mean(rmse_values),
                'rmse_median': np.median(rmse_values),
                'rmse_min': np.min(rmse_values),
                'rmse_max': np.max(rmse_values),
                'rmse_last': rmse_values[-1],
            }
            # Add individual runs
            for i, val in enumerate(rmse_values, 1):
                row[f'run_{i}'] = val
            results.append(row)
            print(f"✓ {dirname}: {len(rmse_values)} runs, median={np.median(rmse_values):.4f}")
        else:
            print(f"✗ {dirname}: No RMSE data found")
    
    return results

# Scan and create DataFrame
print("Scanning m3ed_results directory...\n")
results = scan_results('/media/SSD/m3ed_results')

# Create DataFrame
df = pd.DataFrame(results)

# Reorder columns
base_cols = ['name', 'num_runs', 'rmse_mean', 'rmse_median', 'rmse_min', 'rmse_max', 'rmse_last']
run_cols = [c for c in df.columns if c.startswith('run_')]
run_cols = sorted(run_cols, key=lambda x: int(x.split('_')[1]))
df = df[base_cols + run_cols]

# Save to CSV
output_path = '/media/SSD/vins-dashboard-generator/m3ed_rmse.csv'
df.to_csv(output_path, index=False)

print(f"\n✅ Saved {len(df)} experiments to {output_path}")
print(f"\nVariants found:")
for name in df['name'].unique():
    print(f"  - {name}")
