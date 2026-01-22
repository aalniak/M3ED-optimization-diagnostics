# RMSE Comparison Tables - How To Guide

This document describes how to regenerate and deploy RMSE comparison tables to the M3ED-optimization-diagnostics website.

## Overview

The workflow:
1. Extract RMSE values from experiment results in `/media/SSD/m3ed_results/`
2. Generate HTML comparison tables
3. Push to `gh-pages` branch (used for GitHub Pages rendering)

## Directory Structure

```
/media/SSD/
├── m3ed_results/              # Source: experiment results with results.txt files
├── vins-dashboard-generator/  # Scripts location
│   ├── extract_m3ed_rmse.py   # Extracts RMSE from results.txt files
│   ├── generate_comparison_tables.py  # Generates HTML tables
│   ├── m3ed_rmse.csv          # Generated CSV with all RMSE data
│   └── rmse_tables/           # Generated HTML tables (temporary)
└── M3ED-optimization-diagnostics/  # Git repo for website
    ├── tables/                # RMSE comparison tables
    ├── index.html             # Main dashboard
    └── compare.html           # Interactive comparison tool
```

## Step-by-Step Process

### 1. Extract RMSE Values from Results

```bash
cd /media/SSD/vins-dashboard-generator
python3 extract_m3ed_rmse.py
```

This scans `/media/SSD/m3ed_results/spot_*` directories, parses `results.txt` files, and outputs `m3ed_rmse.csv` with:
- Median, mean, min, max RMSE
- Individual run values

### 2. Generate HTML Comparison Tables

```bash
cd /media/SSD/vins-dashboard-generator
python3 generate_comparison_tables.py
```

This creates tables in `rmse_tables/`:
- `baseline_vs_depth_opt.html` - Baseline vs depth optimization (w100, w500, w1000) and log opt
- `baseline_vs_rgd.html` - Baseline vs RGD (inverse + metric)
- `baseline_vs_mahal.html` - Baseline vs Mahalanobis optimization
- `depth_opt_vs_mahal.html` - Depth opt vs Mahalanobis opt side-by-side
- `baseline_vs_all.html` - Baseline vs all variants
- `index.html` - Index page for tables

### 3. Copy Tables to Repo

```bash
cd /media/SSD/M3ED-optimization-diagnostics
git checkout gh-pages
cp -r /media/SSD/vins-dashboard-generator/rmse_tables/* tables/
```

### 4. Update Main Index (if needed)

The main `index.html` should have a link to tables:
```html
<a href="tables/index.html" class="compare-button" style="background: linear-gradient(135deg, #27ae60, #229954);">📊 RMSE Comparison Tables</a>
```

### 5. Commit and Push to gh-pages

```bash
cd /media/SSD/M3ED-optimization-diagnostics
git checkout gh-pages
git add .
git commit -m "Update RMSE comparison tables"
git push origin gh-pages
```

**Important:** The website is rendered from the `gh-pages` branch, NOT `main` or `master`.

## Adding New Table Configurations

Edit `/media/SSD/vins-dashboard-generator/generate_comparison_tables.py` and modify `tables_config`:

```python
tables_config = [
    {
        'title': 'Table Title',
        'columns': ['base', 'variant1', 'variant2'],  # variant names without sequence prefix
        'filename': 'my_table.html',
        'description': 'Description for index page'
    },
    # ... more tables
]
```

Available variants (as of Jan 2026):
- `base`
- `daac_depth_opt_w100`, `daac_depth_opt_w500`, `daac_depth_opt_w1000`
- `daac_depth_opt_log_w100`
- `daac_depth_opt_mahalanobis_w100`, `daac_depth_opt_mahalanobis_w500`, `daac_depth_opt_mahalanobis_w1000`
- `daac_depth_opt_log_mahalanobis_w30`
- `daac_rgd_inv`, `daac_rgd_metric`

## Table Features

- Uses **median** RMSE values across runs
- Shows **% change vs baseline** in parentheses
- Green highlighting for best value per row
- Color coding: green = improvement, red = degradation
- Outlier threshold: values > 10.0 marked as failures
- Last row shows **average % change** vs baseline for each variant

## Quick One-Liner

To regenerate and deploy everything:

```bash
cd /media/SSD/vins-dashboard-generator && \
python3 extract_m3ed_rmse.py && \
python3 generate_comparison_tables.py && \
cd /media/SSD/M3ED-optimization-diagnostics && \
git checkout gh-pages && \
cp -r /media/SSD/vins-dashboard-generator/rmse_tables/* tables/ && \
git add . && \
git commit -m "Update RMSE tables" && \
git push origin gh-pages
```

## Website URL

https://aalniak.github.io/M3ED-optimization-diagnostics/

Tables: https://aalniak.github.io/M3ED-optimization-diagnostics/tables/
