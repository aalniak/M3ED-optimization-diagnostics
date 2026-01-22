#!/usr/bin/env python3
"""
Generate RMSE comparison tables for different variant combinations.
Uses median RMSE values and shows % change vs baseline.
"""

import pandas as pd
import numpy as np
import os

# Read the CSV data
csv_path = '/media/SSD/vins-dashboard-generator/m3ed_rmse.csv'
df = pd.read_csv(csv_path)

# Extract sequence and variant from name
def parse_name(name):
    """Parse name to extract sequence and variant."""
    # Known variant suffixes - longest first for greedy matching
    variant_markers = [
        '_daac_depth_opt_log_mahalanobis_w50',
        '_daac_depth_opt_log_mahalanobis_w30',
        '_daac_depth_opt_mahalanobis_w1000',
        '_daac_depth_opt_mahalanobis_w500',
        '_daac_depth_opt_mahalanobis_w100',
        '_daac_depth_opt_log_w100',
        '_daac_depth_opt_w1000', 
        '_daac_depth_opt_w500',
        '_daac_depth_opt_w100',
        '_daac_rgd_inv',
        '_daac_rgd_metric',
        '_base',
    ]
    
    for marker in variant_markers:
        if name.endswith(marker):
            seq = name[:-len(marker)]
            variant = marker[1:]  # remove leading underscore
            return seq, variant
    return None, None

# Parse all names
df['sequence'], df['variant'] = zip(*df['name'].apply(parse_name))

# Use rmse_median from CSV (already computed)
# If not present, calculate from run columns
if 'rmse_median' not in df.columns:
    run_cols = [c for c in df.columns if c.startswith('run_')]
    df['rmse_median'] = df[run_cols].median(axis=1)

# Filter out rows with very high RMSE (outliers/failures) - threshold at 10
OUTLIER_THRESHOLD = 10.0

# Pivot to get sequences as rows and variants as columns
pivot_df = df.pivot(index='sequence', columns='variant', values='rmse_median')

# Get unique sequences
sequences = sorted(pivot_df.index.tolist())

def generate_table_html(title, columns, output_file):
    """Generate an HTML comparison table.
    
    Args:
        title: Table title
        columns: List of column names (variants) to include, first should be 'base'
        output_file: Output HTML file path
    """
    # Filter columns that exist
    available_cols = [c for c in columns if c in pivot_df.columns]
    if not available_cols:
        print(f"Warning: No columns available for {title}")
        return
    
    # Create subset dataframe
    table_df = pivot_df[available_cols].copy()
    
    # Calculate % change vs baseline
    if 'base' in available_cols:
        baseline_col = 'base'
        for col in available_cols:
            if col != baseline_col:
                # % change = (new - base) / base * 100
                # Negative means improvement (lower RMSE is better)
                pass  # We'll calculate this in the HTML generation
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px 15px;
            text-align: center;
        }}
        th {{
            background-color: #007bff;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #e9ecef;
        }}
        td:first-child {{
            text-align: left;
            font-weight: 500;
        }}
        .improvement {{
            color: #28a745;
            font-weight: bold;
        }}
        .degradation {{
            color: #dc3545;
            font-weight: bold;
        }}
        .best {{
            background-color: #d4edda !important;
            font-weight: bold;
        }}
        .outlier {{
            color: #999;
            font-style: italic;
        }}
        .avg-row {{
            background-color: #fff3cd !important;
            font-weight: bold;
        }}
        .nav {{
            margin-bottom: 20px;
        }}
        .nav a {{
            margin-right: 15px;
            color: #007bff;
            text-decoration: none;
        }}
        .nav a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="index.html">← Back to Index</a>
    </div>
    <h1>{title}</h1>
    <p>RMSE values (median of runs). Lower is better. Green = best in row. Last row shows average % change vs baseline.</p>
    <table>
        <thead>
            <tr>
                <th>Sequence</th>
"""
    
    # Column headers
    for col in available_cols:
        display_name = col.replace('_', ' ').replace('daac ', '').title()
        html += f"                <th>{display_name}</th>\n"
    
    html += """            </tr>
        </thead>
        <tbody>
"""
    
    # Data rows
    pct_changes = {col: [] for col in available_cols if col != 'base'}
    
    for seq in sequences:
        row_values = {}
        for col in available_cols:
            val = table_df.loc[seq, col] if seq in table_df.index and col in table_df.columns else np.nan
            row_values[col] = val
        
        # Find minimum (best) value in this row
        valid_values = [v for v in row_values.values() if pd.notna(v) and v < OUTLIER_THRESHOLD]
        min_val = min(valid_values) if valid_values else None
        
        html += f"            <tr>\n"
        html += f"                <td>{seq}</td>\n"
        
        baseline_val = row_values.get('base', np.nan)
        
        for col in available_cols:
            val = row_values[col]
            
            if pd.isna(val):
                html += f"                <td>-</td>\n"
            elif val >= OUTLIER_THRESHOLD:
                html += f"                <td class='outlier'>>{OUTLIER_THRESHOLD:.1f}</td>\n"
            else:
                cell_class = ""
                if min_val is not None and abs(val - min_val) < 0.0001:
                    cell_class = "best"
                
                # Calculate % change for non-baseline columns
                if col != 'base' and pd.notna(baseline_val) and baseline_val < OUTLIER_THRESHOLD and val < OUTLIER_THRESHOLD:
                    pct_change = ((val - baseline_val) / baseline_val) * 100
                    pct_changes[col].append(pct_change)
                    
                    if pct_change < -1:  # More than 1% improvement
                        pct_class = "improvement"
                    elif pct_change > 1:  # More than 1% degradation
                        pct_class = "degradation"
                    else:
                        pct_class = ""
                    
                    html += f"                <td class='{cell_class}'>{val:.4f} <span class='{pct_class}'>({pct_change:+.1f}%)</span></td>\n"
                else:
                    html += f"                <td class='{cell_class}'>{val:.4f}</td>\n"
        
        html += f"            </tr>\n"
    
    # Average % change row
    html += f"            <tr class='avg-row'>\n"
    html += f"                <td><strong>Avg % Change vs Base</strong></td>\n"
    html += f"                <td>-</td>\n"  # baseline column
    
    for col in available_cols:
        if col == 'base':
            continue
        if pct_changes[col]:
            avg_pct = np.mean(pct_changes[col])
            pct_class = "improvement" if avg_pct < -1 else ("degradation" if avg_pct > 1 else "")
            html += f"                <td class='{pct_class}'><strong>{avg_pct:+.2f}%</strong></td>\n"
        else:
            html += f"                <td>-</td>\n"
    
    html += """            </tr>
        </tbody>
    </table>
</body>
</html>
"""
    
    # Write file
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Generated: {output_file}")

def generate_index_html(tables, output_dir):
    """Generate index HTML with links to all tables."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M3ED RMSE Comparison Tables</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
        }
        .card {
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card h2 {
            margin-top: 0;
            color: #007bff;
        }
        .card a {
            color: #007bff;
            text-decoration: none;
            font-weight: 500;
        }
        .card a:hover {
            text-decoration: underline;
        }
        .card p {
            color: #666;
            margin-bottom: 0;
        }
    </style>
</head>
<body>
    <h1>M3ED RMSE Comparison Tables</h1>
    <p>Comparison tables using median RMSE values across runs.</p>
"""
    
    for title, filename, description in tables:
        html += f"""
    <div class="card">
        <h2><a href="{filename}">{title}</a></h2>
        <p>{description}</p>
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w') as f:
        f.write(html)
    print(f"Generated: {index_path}")

# Output directory
output_dir = '/media/SSD/vins-dashboard-generator/rmse_tables'
os.makedirs(output_dir, exist_ok=True)

# Define table configurations
tables_config = [
    {
        'title': 'Baseline vs Depth Optimization (and Log Opt)',
        'columns': ['base', 'daac_depth_opt_w100', 'daac_depth_opt_w500', 'daac_depth_opt_w1000', 'daac_depth_opt_log_w100'],
        'filename': 'baseline_vs_depth_opt.html',
        'description': 'Comparison of baseline with depth optimization variants (w100, w500, w1000) and log optimization.'
    },
    {
        'title': 'Baseline vs RGD (Inverse + Metric)',
        'columns': ['base', 'daac_rgd_inv', 'daac_rgd_metric'],
        'filename': 'baseline_vs_rgd.html',
        'description': 'Comparison of baseline with inverse depth RGD and metric RGD variants.'
    },
    {
        'title': 'Baseline vs Mahalanobis Optimization',
        'columns': ['base', 'daac_depth_opt_mahalanobis_w100', 'daac_depth_opt_mahalanobis_w500', 
                   'daac_depth_opt_mahalanobis_w1000', 'daac_depth_opt_log_mahalanobis_w30'],
        'filename': 'baseline_vs_mahal.html',
        'description': 'Comparison of baseline with Mahalanobis depth optimization variants.'
    },
    {
        'title': 'Depth Opt vs Mahalanobis Opt',
        'columns': ['base', 'daac_depth_opt_w100', 'daac_depth_opt_mahalanobis_w100', 
                   'daac_depth_opt_w500', 'daac_depth_opt_mahalanobis_w500',
                   'daac_depth_opt_w1000', 'daac_depth_opt_mahalanobis_w1000'],
        'filename': 'depth_opt_vs_mahal.html',
        'description': 'Side-by-side comparison of regular depth optimization vs Mahalanobis optimization.'
    },
    {
        'title': 'Baseline vs All Variants',
        'columns': ['base', 'daac_depth_opt_w100', 'daac_depth_opt_w500', 'daac_depth_opt_w1000', 
                   'daac_depth_opt_log_w100', 'daac_depth_opt_mahalanobis_w100', 
                   'daac_depth_opt_mahalanobis_w500', 'daac_depth_opt_mahalanobis_w1000',
                   'daac_depth_opt_log_mahalanobis_w30', 'daac_rgd_inv', 'daac_rgd_metric'],
        'filename': 'baseline_vs_all.html',
        'description': 'Comparison of baseline with all available variants.'
    },
]

# Generate tables
tables_list = []
for config in tables_config:
    output_path = os.path.join(output_dir, config['filename'])
    generate_table_html(config['title'], config['columns'], output_path)
    tables_list.append((config['title'], config['filename'], config['description']))

# Generate index
generate_index_html(tables_list, output_dir)

print(f"\n✅ All tables generated in {output_dir}")
print(f"To view, open: file://{output_dir}/index.html")
