#!/usr/bin/env python3
"""
Bitaxe Historic Data Analysis Generator

Analyzes last 24 hours of monitoring data to identify optimal settings
for efficiency and low variance. Generates comprehensive HTML report
with 3D visualizations and recommendations.

Author: mtab3000
License: MIT
"""

import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import logging
from typing import Dict, List, Tuple, Optional
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_to_json_serializable(obj):
    """Convert numpy types to JSON-serializable Python types"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(v) for v in obj]
    else:
        return obj

class BitaxeAnalyzer:
    """Analyzes Bitaxe monitoring data and generates comprehensive reports"""
    
    def __init__(self, data_dir: str = None, output_dir: str = "../generated_charts"):
        # Smart data directory detection
        if data_dir is None:
            self.data_dirs = self._detect_data_directories()
        else:
            self.data_dirs = [Path(data_dir)]
            
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configuration options
        self.min_measurements = 5
        self.export_csv = False
        
        # Column mapping for different CSV formats
        self.column_mapping = {
            'set_voltage_v': ['set_voltage_v', 'core_voltage_set_v'],
            'frequency_mhz': ['frequency_mhz'],
            'hashrate_th': ['hashrate_th'],
            'efficiency_j_th': ['efficiency_j_th', 'efficiency_jth'],
            'actual_voltage_v': ['actual_voltage_v', 'core_voltage_actual_v'],
            'power_w': ['power_w'],
            'asic_temp_c': ['asic_temp_c', 'temperature_c'],
            'fan_speed_rpm': ['fan_speed_rpm'],
            'fan_speed_percent': ['fan_speed_percent']
        }
            
        logger.info(f"Initialized analyzer: data_dirs={[str(d) for d in self.data_dirs]}, output='{self.output_dir}'")
        
    def _detect_data_directories(self) -> List[Path]:
        """Detect possible data directories in order of preference"""
        possible_dirs = []
        
        # Current working directory (for when run from main directory)
        cwd = Path.cwd()
        possible_dirs.append(cwd)
        
        # Parent directory (for when run from scripts directory) 
        parent_dir = cwd.parent
        possible_dirs.append(parent_dir)
        
        # Traditional data directory relative to scripts
        possible_dirs.append(Path("../data"))
        
        # Absolute data directory relative to parent
        possible_dirs.append(parent_dir / "data")
        
        # Docker data directory (if specified in environment)
        docker_data_dir = os.getenv('DATA_DIR')
        if docker_data_dir:
            possible_dirs.append(Path(docker_data_dir))
            
        # Filter to existing directories and log findings
        existing_dirs = []
        for dir_path in possible_dirs:
            if dir_path.exists():
                existing_dirs.append(dir_path)
                logger.debug(f"Found data directory: {dir_path}")
            else:
                logger.debug(f"Data directory not found: {dir_path}")
                
        if not existing_dirs:
            # Create default data directory
            default_dir = Path("../data")
            default_dir.mkdir(parents=True, exist_ok=True)
            existing_dirs.append(default_dir)
            logger.warning(f"No data directories found, created: {default_dir}")
            
        return existing_dirs
        
    def find_latest_csv(self) -> Optional[Path]:
        """Find the most recent CSV file across all data directories"""
        all_csv_files = []
        
        # Search all possible data directories
        for data_dir in self.data_dirs:
            if data_dir.exists():
                csv_files = list(data_dir.glob("*.csv"))
                for csv_file in csv_files:
                    logger.debug(f"Found CSV: {csv_file} (size: {csv_file.stat().st_size} bytes)")
                all_csv_files.extend(csv_files)
        
        if not all_csv_files:
            logger.error(f"No CSV files found in any data directories: {[str(d) for d in self.data_dirs]}")
            return None
        
        # Sort by modification time and return the latest
        latest_file = max(all_csv_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Using most recent data file: {latest_file}")
        logger.info(f"File size: {latest_file.stat().st_size} bytes, modified: {datetime.fromtimestamp(latest_file.stat().st_mtime)}")
        return latest_file
        
    def load_and_filter_data(self, csv_file: Path, hours: int = 24) -> pd.DataFrame:
        """Load CSV data and filter for specified time window"""
        try:
            logger.info(f"Loading data from: {csv_file}")
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded {len(df)} records from {csv_file}")
            
            if df.empty:
                logger.warning("CSV file is empty")
                return pd.DataFrame()
            
            # Map column names to standardized format
            df = self._standardize_columns(df)
            
            # Validate required columns after mapping
            required_columns = ['timestamp', 'miner_name', 'set_voltage_v', 'frequency_mhz', 
                              'hashrate_th', 'efficiency_j_th']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                logger.info(f"Available columns: {list(df.columns)}")
                return pd.DataFrame()
            
            # Convert timestamp to datetime with error handling
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except Exception as e:
                logger.error(f"Failed to parse timestamps: {e}")
                return pd.DataFrame()
            
            # Filter for last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours)
            df_filtered = df[df['timestamp'] >= cutoff_time].copy()
            
            logger.info(f"Filtered to {len(df_filtered)} records from last {hours} hours")
            
            if df_filtered.empty:
                logger.warning(f"No data found within the last {hours} hours")
                logger.info(f"Data time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            
            return df_filtered
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file}")
            return pd.DataFrame()
        except pd.errors.EmptyDataError:
            logger.error(f"CSV file is empty: {csv_file}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to expected format"""
        original_columns = list(df.columns)
        
        for standard_name, possible_names in self.column_mapping.items():
            for possible_name in possible_names:
                if possible_name in df.columns and standard_name not in df.columns:
                    df = df.rename(columns={possible_name: standard_name})
                    logger.debug(f"Mapped column: {possible_name} -> {standard_name}")
                    break
        
        # Add missing columns with default values if needed
        if 'fan_speed_percent' not in df.columns and 'fan_speed_rpm' in df.columns:
            # Estimate fan percentage (assuming max RPM around 6000)
            df['fan_speed_percent'] = (df['fan_speed_rpm'] / 6000 * 100).clip(0, 100)
            logger.debug("Generated fan_speed_percent from fan_speed_rpm")
        
        logger.debug(f"Column mapping: {original_columns} -> {list(df.columns)}")
        return df
    
    def analyze_miner_performance(self, df: pd.DataFrame, miner_name: str) -> Dict:
        """Analyze performance metrics for a specific miner"""
        # Check if dataframe is empty or missing required columns
        if df.empty:
            return {"error": f"No data available"}
            
        required_columns = ['miner_name', 'set_voltage_v', 'frequency_mhz', 'hashrate_th', 'efficiency_j_th']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {"error": f"Missing required columns: {missing_columns}"}
        
        miner_data = df[df['miner_name'] == miner_name].copy()
        
        if miner_data.empty:
            return {"error": f"No data found for {miner_name}"}
        
        # Group by set voltage and frequency to find patterns
        grouped = miner_data.groupby(['set_voltage_v', 'frequency_mhz']).agg({
            'hashrate_th': ['mean', 'std', 'count'],
            'efficiency_j_th': ['mean', 'std'],
            'actual_voltage_v': 'mean',
            'power_w': 'mean',
            'asic_temp_c': 'mean',
            'fan_speed_rpm': 'mean',
            'fan_speed_percent': 'mean'
        }).round(3)
        
        # Flatten column names
        grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
        grouped = grouped.reset_index()
        
        # Calculate variance as percentage
        grouped['hashrate_variance_pct'] = (grouped['hashrate_th_std'] / grouped['hashrate_th_mean'] * 100).round(1)
        
        # Only include combinations with sufficient data points
        grouped = grouped[grouped['hashrate_th_count'] >= self.min_measurements].copy()
        
        if grouped.empty:
            return {"error": f"Insufficient data for analysis of {miner_name}"}
        
        # Find optimal settings
        best_efficiency = grouped.loc[grouped['efficiency_j_th_mean'].idxmin()]
        best_stability = grouped.loc[grouped['hashrate_variance_pct'].idxmin()]
        best_hashrate = grouped.loc[grouped['hashrate_th_mean'].idxmax()]
        
        # Find balanced recommendation (good efficiency + low variance)
        # Weight efficiency and stability equally
        grouped['efficiency_rank'] = grouped['efficiency_j_th_mean'].rank()
        grouped['stability_rank'] = grouped['hashrate_variance_pct'].rank()
        grouped['combined_score'] = grouped['efficiency_rank'] + grouped['stability_rank']
        best_balanced = grouped.loc[grouped['combined_score'].idxmin()]
        
        # Determine if settings are "quiet" (fan < 60%)
        grouped['is_quiet'] = grouped['fan_speed_percent_mean'] <= 60
        quiet_options = grouped[grouped['is_quiet']]
        
        analysis = {
            'miner_name': miner_name,
            'total_measurements': len(miner_data),
            'unique_settings': len(grouped),
            'time_range': {
                'start': miner_data['timestamp'].min().strftime('%Y-%m-%d %H:%M'),
                'end': miner_data['timestamp'].max().strftime('%Y-%m-%d %H:%M')
            },
            'all_combinations': grouped.to_dict('records'),
            'recommendations': {
                'best_efficiency': {
                    'set_voltage_mv': int(best_efficiency['set_voltage_v'] * 1000),
                    'frequency_mhz': int(best_efficiency['frequency_mhz']),
                    'hashrate_th': best_efficiency['hashrate_th_mean'],
                    'efficiency_j_th': best_efficiency['efficiency_j_th_mean'],
                    'variance_pct': best_efficiency['hashrate_variance_pct'],
                    'fan_percent': best_efficiency['fan_speed_percent_mean'],
                    'is_quiet': bool(best_efficiency['fan_speed_percent_mean'] <= 60),
                    'actual_voltage_v': best_efficiency['actual_voltage_v_mean']
                },
                'best_stability': {
                    'set_voltage_mv': int(best_stability['set_voltage_v'] * 1000),
                    'frequency_mhz': int(best_stability['frequency_mhz']),
                    'hashrate_th': best_stability['hashrate_th_mean'],
                    'efficiency_j_th': best_stability['efficiency_j_th_mean'],
                    'variance_pct': best_stability['hashrate_variance_pct'],
                    'fan_percent': best_stability['fan_speed_percent_mean'],
                    'is_quiet': bool(best_stability['fan_speed_percent_mean'] <= 60),
                    'actual_voltage_v': best_stability['actual_voltage_v_mean']
                },
                'best_hashrate': {
                    'set_voltage_mv': int(best_hashrate['set_voltage_v'] * 1000),
                    'frequency_mhz': int(best_hashrate['frequency_mhz']),
                    'hashrate_th': best_hashrate['hashrate_th_mean'],
                    'efficiency_j_th': best_hashrate['efficiency_j_th_mean'],
                    'variance_pct': best_hashrate['hashrate_variance_pct'],
                    'fan_percent': best_hashrate['fan_speed_percent_mean'],
                    'is_quiet': bool(best_hashrate['fan_speed_percent_mean'] <= 60),
                    'actual_voltage_v': best_hashrate['actual_voltage_v_mean']
                },
                'best_balanced': {
                    'set_voltage_mv': int(best_balanced['set_voltage_v'] * 1000),
                    'frequency_mhz': int(best_balanced['frequency_mhz']),
                    'hashrate_th': best_balanced['hashrate_th_mean'],
                    'efficiency_j_th': best_balanced['efficiency_j_th_mean'],
                    'variance_pct': best_balanced['hashrate_variance_pct'],
                    'fan_percent': best_balanced['fan_speed_percent_mean'],
                    'is_quiet': bool(best_balanced['fan_speed_percent_mean'] <= 60),
                    'actual_voltage_v': best_balanced['actual_voltage_v_mean']
                }
            },
            'quiet_analysis': {
                'total_quiet_settings': len(quiet_options),
                'total_settings': len(grouped),
                'quiet_percentage': round(len(quiet_options) / len(grouped) * 100, 1) if len(grouped) > 0 else 0,
                'best_quiet_efficiency': quiet_options.loc[quiet_options['efficiency_j_th_mean'].idxmin()].to_dict() if not quiet_options.empty else None
            }
        }
        
        return analysis
    
    def generate_html_report(self, analyses: List[Dict], hours: int = 24) -> str:
        """Generate comprehensive HTML report with 3D visualizations"""
        
        # Extract data for JavaScript
        js_data = {}
        for analysis in analyses:
            if 'error' not in analysis:
                miner_name = analysis['miner_name'].lower().replace('-', '')
                js_data[miner_name] = {
                    'combinations': analysis['all_combinations'],
                    'recommendations': analysis['recommendations'],
                    'quiet_analysis': analysis['quiet_analysis']
                }
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self' https://cdnjs.cloudflare.com;">
    <title>Bitaxe Performance Analysis - Last {hours}h</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.26.0/plotly.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 15px;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1900px;
            margin: 0 auto;
            background: rgba(20, 20, 20, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        }}
        h1 {{
            text-align: center;
            background: linear-gradient(45deg, #00ff88, #00ccff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }}
        .analysis-header {{
            background: linear-gradient(135deg, #ff6b6b, #ffd93d);
            color: #000;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
            font-size: 1.2em;
            border: 3px solid #00ff88;
        }}
        .time-range {{
            background: linear-gradient(135deg, #17a2b8, #007bff);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
        }}
        .champion-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .champion-card {{
            padding: 20px;
            border-radius: 12px;
            border: 3px solid;
            text-align: center;
        }}
        .champion-card.efficiency {{
            background: linear-gradient(135deg, #4ecdc4, #44a08d);
            border-color: #4ecdc4;
        }}
        .champion-card.stability {{
            background: linear-gradient(135deg, #a8edea, #fed6e3);
            color: #000;
            border-color: #a8edea;
        }}
        .champion-card.hashrate {{
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            border-color: #ff6b6b;
        }}
        .champion-card.balanced {{
            background: linear-gradient(135deg, #ffecd2, #fcb69f);
            color: #000;
            border-color: #ffc107;
        }}
        .miner-section {{
            margin-bottom: 40px;
            background: rgba(30, 30, 30, 0.9);
            border-radius: 15px;
            padding: 25px;
            border: 3px solid;
        }}
        .miner-1 {{ border-color: #e74c3c; }}
        .miner-2 {{ border-color: #f39c12; }}
        .miner-3 {{ border-color: #2ecc71; }}
        .miner-title {{
            font-size: 1.8em;
            margin-bottom: 15px;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }}
        .miner-1 .miner-title {{ color: #e74c3c; }}
        .miner-2 .miner-title {{ color: #f39c12; }}
        .miner-3 .miner-title {{ color: #2ecc71; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: rgba(40, 40, 40, 0.9);
            padding: 18px;
            border-radius: 10px;
            border-left: 4px solid #00ff88;
        }}
        .metric {{
            margin: 8px 0;
            font-size: 0.95em;
        }}
        .metric strong {{
            color: #00ff88;
        }}
        .plot-container {{
            height: 550px;
            margin: 15px 0;
            background: rgba(40, 40, 40, 0.4);
            border-radius: 10px;
            padding: 10px;
        }}
        .recommendations {{
            background: linear-gradient(135deg, #155724, #28a745);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin: 25px 0;
            border: 4px solid #00ff88;
        }}
        .rec-item {{
            margin: 15px 0;
            padding: 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }}
        .quiet-analysis {{
            background: linear-gradient(135deg, #6610f2, #6f42c1);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .no-data-warning {{
            background: linear-gradient(135deg, #dc3545, #c82333);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            text-align: center;
        }}
        .settings-highlight {{
            background: rgba(255, 215, 0, 0.2);
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #ffd700;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ BITAXE PERFORMANCE ANALYSIS</h1>
        
        <div class="analysis-header">
            <h2>📊 HISTORIC DATA ANALYSIS - LAST {hours} HOURS</h2>
            <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Data Source:</strong> Live monitoring data with voltage/frequency optimization tracking</p>
        </div>

        <div class="time-range">
            <h3>🕒 Analysis Time Window</h3>
"""

        # Add time range for each miner
        for analysis in analyses:
            if 'error' not in analysis:
                time_info = analysis['time_range']
                html_template += f"""
            <p><strong>{analysis['miner_name']}:</strong> {time_info['start']} → {time_info['end']} 
            ({analysis['total_measurements']} measurements, {analysis['unique_settings']} unique settings)</p>
"""

        html_template += """
        </div>
"""

        # Find overall champions
        all_efficiency = []
        all_stability = []
        all_hashrate = []
        all_balanced = []
        
        for analysis in analyses:
            if 'error' not in analysis:
                recs = analysis['recommendations']
                all_efficiency.append((analysis['miner_name'], recs['best_efficiency']))
                all_stability.append((analysis['miner_name'], recs['best_stability']))
                all_hashrate.append((analysis['miner_name'], recs['best_hashrate']))
                all_balanced.append((analysis['miner_name'], recs['best_balanced']))

        if all_efficiency:
            best_eff = min(all_efficiency, key=lambda x: x[1]['efficiency_j_th'])
            best_stab = min(all_stability, key=lambda x: x[1]['variance_pct'])
            best_hash = max(all_hashrate, key=lambda x: x[1]['hashrate_th'])
            # For balanced, use efficiency rank + stability rank
            best_bal = min(all_balanced, key=lambda x: x[1]['efficiency_j_th'] + x[1]['variance_pct'])

            html_template += f"""
        <div class="champion-grid">
            <div class="champion-card efficiency">
                <h4>⚡ EFFICIENCY CHAMPION</h4>
                <div style="font-size: 1.3em; margin: 10px 0;"><strong>{best_eff[0]}</strong></div>
                <div style="font-size: 1.5em; color: #ffff00;"><strong>{best_eff[1]['efficiency_j_th']:.2f} J/TH</strong></div>
                <div>SET {best_eff[1]['set_voltage_mv']}mV @ {best_eff[1]['frequency_mhz']}MHz</div>
                <div>{best_eff[1]['hashrate_th']:.2f} TH/s, ±{best_eff[1]['variance_pct']:.1f}% variance</div>
                <div>{'🔇 QUIET' if best_eff[1]['is_quiet'] else '🔊 LOUD'} ({best_eff[1]['fan_percent']:.1f}% fan)</div>
            </div>
            <div class="champion-card stability">
                <h4>🎯 STABILITY CHAMPION</h4>
                <div style="font-size: 1.3em; margin: 10px 0;"><strong>{best_stab[0]}</strong></div>
                <div style="font-size: 1.5em; color: #007bff;"><strong>±{best_stab[1]['variance_pct']:.1f}%</strong></div>
                <div>SET {best_stab[1]['set_voltage_mv']}mV @ {best_stab[1]['frequency_mhz']}MHz</div>
                <div>{best_stab[1]['hashrate_th']:.2f} TH/s, {best_stab[1]['efficiency_j_th']:.2f} J/TH</div>
                <div>{'🔇 QUIET' if best_stab[1]['is_quiet'] else '🔊 LOUD'} ({best_stab[1]['fan_percent']:.1f}% fan)</div>
            </div>
            <div class="champion-card hashrate">
                <h4>🚀 HASHRATE CHAMPION</h4>
                <div style="font-size: 1.3em; margin: 10px 0;"><strong>{best_hash[0]}</strong></div>
                <div style="font-size: 1.5em; color: #ffff00;"><strong>{best_hash[1]['hashrate_th']:.2f} TH/s</strong></div>
                <div>SET {best_hash[1]['set_voltage_mv']}mV @ {best_hash[1]['frequency_mhz']}MHz</div>
                <div>{best_hash[1]['efficiency_j_th']:.2f} J/TH, ±{best_hash[1]['variance_pct']:.1f}% variance</div>
                <div>{'🔇 QUIET' if best_hash[1]['is_quiet'] else '🔊 LOUD'} ({best_hash[1]['fan_percent']:.1f}% fan)</div>
            </div>
            <div class="champion-card balanced">
                <h4>⚖️ BALANCED CHAMPION</h4>
                <div style="font-size: 1.3em; margin: 10px 0;"><strong>{best_bal[0]}</strong></div>
                <div style="font-size: 1.2em; color: #007bff;">{best_bal[1]['efficiency_j_th']:.2f} J/TH, ±{best_bal[1]['variance_pct']:.1f}%</div>
                <div>SET {best_bal[1]['set_voltage_mv']}mV @ {best_bal[1]['frequency_mhz']}MHz</div>
                <div>{best_bal[1]['hashrate_th']:.2f} TH/s</div>
                <div>{'🔇 QUIET' if best_bal[1]['is_quiet'] else '🔊 LOUD'} ({best_bal[1]['fan_percent']:.1f}% fan)</div>
            </div>
        </div>
"""

        # Add individual miner sections
        miner_classes = ['miner-1', 'miner-2', 'miner-3']
        for i, analysis in enumerate(analyses):
            if 'error' in analysis:
                html_template += f"""
        <div class="miner-section {miner_classes[i]}">
            <h2 class="miner-title">{analysis.get('miner_name', f'Miner-{i+1}')} - NO DATA</h2>
            <div class="no-data-warning">
                <strong>⚠️ INSUFFICIENT DATA</strong><br>
                {analysis['error']}
            </div>
        </div>
"""
                continue
            
            recs = analysis['recommendations']
            quiet = analysis['quiet_analysis']
            
            html_template += f"""
        <div class="miner-section {miner_classes[i]}">
            <h2 class="miner-title">{analysis['miner_name']} - PERFORMANCE ANALYSIS</h2>
            
            <div class="quiet-analysis">
                <h3>🔇 QUIET OPERATION ANALYSIS</h3>
                <p><strong>Quiet Settings Available:</strong> {quiet['total_quiet_settings']}/{quiet['total_settings']} ({quiet['quiet_percentage']}%)</p>
"""
            
            if quiet['best_quiet_efficiency']:
                best_quiet = quiet['best_quiet_efficiency']
                html_template += f"""
                <div class="settings-highlight">
                    <strong>Best Quiet Option:</strong> SET {int(best_quiet['set_voltage_v']*1000)}mV @ {int(best_quiet['frequency_mhz'])}MHz<br>
                    Performance: {best_quiet['hashrate_th_mean']:.2f} TH/s, {best_quiet['efficiency_j_th_mean']:.2f} J/TH, ±{best_quiet['hashrate_variance_pct']:.1f}%<br>
                    Fan: {best_quiet['fan_speed_percent_mean']:.1f}% (QUIET)
                </div>
"""
            else:
                html_template += """
                <div class="no-data-warning">No quiet settings found - all combinations result in >60% fan speed</div>
"""
            
            html_template += """
            </div>
            
            <div class="summary-grid">
                <div class="summary-card">
                    <h4>⚡ Best Efficiency</h4>
"""
            
            rec = recs['best_efficiency']
            html_template += f"""
                    <div class="metric"><strong>Setting:</strong> SET {rec['set_voltage_mv']}mV @ {rec['frequency_mhz']}MHz</div>
                    <div class="metric"><strong>Performance:</strong> {rec['hashrate_th']:.2f} TH/s, {rec['efficiency_j_th']:.2f} J/TH</div>
                    <div class="metric"><strong>Stability:</strong> ±{rec['variance_pct']:.1f}% variance</div>
                    <div class="metric"><strong>Fan:</strong> {rec['fan_percent']:.1f}% ({'QUIET' if rec['is_quiet'] else 'LOUD'})</div>
                    <div class="metric"><strong>Actual Voltage:</strong> {rec['actual_voltage_v']:.3f}V</div>
                </div>
                <div class="summary-card">
                    <h4>🎯 Best Stability</h4>
"""
            
            rec = recs['best_stability']
            html_template += f"""
                    <div class="metric"><strong>Setting:</strong> SET {rec['set_voltage_mv']}mV @ {rec['frequency_mhz']}MHz</div>
                    <div class="metric"><strong>Performance:</strong> {rec['hashrate_th']:.2f} TH/s, {rec['efficiency_j_th']:.2f} J/TH</div>
                    <div class="metric"><strong>Stability:</strong> ±{rec['variance_pct']:.1f}% variance</div>
                    <div class="metric"><strong>Fan:</strong> {rec['fan_percent']:.1f}% ({'QUIET' if rec['is_quiet'] else 'LOUD'})</div>
                    <div class="metric"><strong>Actual Voltage:</strong> {rec['actual_voltage_v']:.3f}V</div>
                </div>
                <div class="summary-card">
                    <h4>🚀 Best Hashrate</h4>
"""
            
            rec = recs['best_hashrate']
            html_template += f"""
                    <div class="metric"><strong>Setting:</strong> SET {rec['set_voltage_mv']}mV @ {rec['frequency_mhz']}MHz</div>
                    <div class="metric"><strong>Performance:</strong> {rec['hashrate_th']:.2f} TH/s, {rec['efficiency_j_th']:.2f} J/TH</div>
                    <div class="metric"><strong>Stability:</strong> ±{rec['variance_pct']:.1f}% variance</div>
                    <div class="metric"><strong>Fan:</strong> {rec['fan_percent']:.1f}% ({'QUIET' if rec['is_quiet'] else 'LOUD'})</div>
                    <div class="metric"><strong>Actual Voltage:</strong> {rec['actual_voltage_v']:.3f}V</div>
                </div>
                <div class="summary-card">
                    <h4>⚖️ Best Balanced</h4>
"""
            
            rec = recs['best_balanced']
            html_template += f"""
                    <div class="metric"><strong>Setting:</strong> SET {rec['set_voltage_mv']}mV @ {rec['frequency_mhz']}MHz</div>
                    <div class="metric"><strong>Performance:</strong> {rec['hashrate_th']:.2f} TH/s, {rec['efficiency_j_th']:.2f} J/TH</div>
                    <div class="metric"><strong>Stability:</strong> ±{rec['variance_pct']:.1f}% variance</div>
                    <div class="metric"><strong>Fan:</strong> {rec['fan_percent']:.1f}% ({'QUIET' if rec['is_quiet'] else 'LOUD'})</div>
                    <div class="metric"><strong>Actual Voltage:</strong> {rec['actual_voltage_v']:.3f}V</div>
                </div>
            </div>
            
            <div class="plot-container" id="{analysis['miner_name'].lower().replace('-', '')}-hashrate-surface"></div>
            <div class="plot-container" id="{analysis['miner_name'].lower().replace('-', '')}-efficiency-surface"></div>
            <div class="plot-container" id="{analysis['miner_name'].lower().replace('-', '')}-stability-surface"></div>
            <div class="plot-container" id="{analysis['miner_name'].lower().replace('-', '')}-correlation"></div>
        </div>
"""

        # Add final recommendations
        html_template += """
        <div class="recommendations">
            <h3>🎯 FINAL RECOMMENDATIONS</h3>
            
            <div class="rec-item">
                <strong>🏆 FOR MAXIMUM EFFICIENCY (Cost Optimization):</strong><br>
"""
        
        if all_efficiency:
            best_eff = min(all_efficiency, key=lambda x: x[1]['efficiency_j_th'])
            rec = best_eff[1]
            html_template += f"""
                {best_eff[0]}: SET {rec['set_voltage_mv']}mV @ {rec['frequency_mhz']}MHz → {rec['hashrate_th']:.2f} TH/s, {rec['efficiency_j_th']:.2f} J/TH, ±{rec['variance_pct']:.1f}% variance<br>
                <em>{'Quiet operation' if rec['is_quiet'] else 'Loud operation'} ({rec['fan_percent']:.1f}% fan)</em>
"""
        
        html_template += """
            </div>
            
            <div class="rec-item">
                <strong>🎯 FOR MAXIMUM STABILITY (Reliability Priority):</strong><br>
"""
        
        if all_stability:
            best_stab = min(all_stability, key=lambda x: x[1]['variance_pct'])
            rec = best_stab[1]
            html_template += f"""
                {best_stab[0]}: SET {rec['set_voltage_mv']}mV @ {rec['frequency_mhz']}MHz → {rec['hashrate_th']:.2f} TH/s, {rec['efficiency_j_th']:.2f} J/TH, ±{rec['variance_pct']:.1f}% variance<br>
                <em>{'Quiet operation' if rec['is_quiet'] else 'Loud operation'} ({rec['fan_percent']:.1f}% fan)</em>
"""
        
        html_template += """
            </div>
            
            <div class="rec-item">
                <strong>🚀 FOR MAXIMUM HASHRATE (Performance Priority):</strong><br>
"""
        
        if all_hashrate:
            best_hash = max(all_hashrate, key=lambda x: x[1]['hashrate_th'])
            rec = best_hash[1]
            html_template += f"""
                {best_hash[0]}: SET {rec['set_voltage_mv']}mV @ {rec['frequency_mhz']}MHz → {rec['hashrate_th']:.2f} TH/s, {rec['efficiency_j_th']:.2f} J/TH, ±{rec['variance_pct']:.1f}% variance<br>
                <em>{'Quiet operation' if rec['is_quiet'] else 'Loud operation'} ({rec['fan_percent']:.1f}% fan)</em>
"""
        
        html_template += """
            </div>
            
            <div class="rec-item">
                <strong>⚖️ FOR BALANCED OPERATION (Recommended):</strong><br>
"""
        
        if all_balanced:
            best_bal = min(all_balanced, key=lambda x: x[1]['efficiency_j_th'] + x[1]['variance_pct'])
            rec = best_bal[1]
            html_template += f"""
                {best_bal[0]}: SET {rec['set_voltage_mv']}mV @ {rec['frequency_mhz']}MHz → {rec['hashrate_th']:.2f} TH/s, {rec['efficiency_j_th']:.2f} J/TH, ±{rec['variance_pct']:.1f}% variance<br>
                <em>{'Quiet operation' if rec['is_quiet'] else 'Loud operation'} ({rec['fan_percent']:.1f}% fan)</em>
"""
        
        html_template += """
            </div>
        </div>
    </div>

    <script>
        // Data for JavaScript visualizations
        const analysisData = """ + json.dumps(convert_to_json_serializable(js_data)) + """;
        
        // Enhanced 3D Surface Plot Generation
        function create3DSurface(containerId, title, minerKey, zField, colorScale, zTitle) {
            if (!analysisData[minerKey] || !analysisData[minerKey].combinations) {
                return;
            }
            
            const data = analysisData[minerKey].combinations;
            
            // Get unique frequencies and voltages
            const frequencies = [...new Set(data.map(d => d.frequency_mhz))].sort((a,b) => a-b);
            const voltages = [...new Set(data.map(d => d.set_voltage_v * 1000))].sort((a,b) => a-b);
            
            // Create Z matrix
            const zData = frequencies.map(freq => 
                voltages.map(volt => {
                    const point = data.find(d => 
                        d.frequency_mhz === freq && Math.abs(d.set_voltage_v * 1000 - volt) < 1
                    );
                    return point ? point[zField] : null;
                })
            );

            const trace = {
                z: zData,
                x: voltages,
                y: frequencies,
                type: 'surface',
                colorscale: colorScale,
                colorbar: {
                    title: zTitle,
                    titleside: 'right'
                }
            };

            const layout = {
                title: {
                    text: title,
                    font: { color: '#ffffff', size: 14 }
                },
                scene: {
                    xaxis: { title: 'SET Voltage (mV)', color: '#ffffff' },
                    yaxis: { title: 'Frequency (MHz)', color: '#ffffff' },
                    zaxis: { title: zTitle, color: '#ffffff' },
                    bgcolor: 'rgba(0,0,0,0)',
                    camera: { eye: { x: 1.3, y: 1.3, z: 1.3 } }
                },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#ffffff' }
            };

            Plotly.newPlot(containerId, [trace], layout, {responsive: true});
        }

        // Create correlation plot (efficiency vs stability vs actual voltage)
        function createCorrelationPlot(containerId, title, minerKey) {
            if (!analysisData[minerKey] || !analysisData[minerKey].combinations) {
                return;
            }
            
            const data = analysisData[minerKey].combinations;

            const trace = {
                x: data.map(d => d.efficiency_j_th_mean),
                y: data.map(d => d.hashrate_variance_pct),
                z: data.map(d => d.actual_voltage_v_mean),
                mode: 'markers',
                type: 'scatter3d',
                marker: {
                    size: 10,
                    color: data.map(d => d.actual_voltage_v_mean),
                    colorscale: 'Viridis',
                    colorbar: {
                        title: 'Actual Voltage (V)',
                        titleside: 'right'
                    }
                },
                text: data.map(d => `SET ${(d.set_voltage_v*1000).toFixed(0)}mV @ ${d.frequency_mhz}MHz`),
                hovertemplate: '%{text}<br>Efficiency: %{x:.2f} J/TH<br>Stability: ±%{y:.1f}%<br>Actual: %{z:.3f}V<extra></extra>'
            };

            const layout = {
                title: {
                    text: title,
                    font: { color: '#ffffff', size: 14 }
                },
                scene: {
                    xaxis: { title: 'Efficiency (J/TH)', color: '#ffffff' },
                    yaxis: { title: 'Stability (±% variance)', color: '#ffffff' },
                    zaxis: { title: 'Actual Voltage (V)', color: '#ffffff' },
                    bgcolor: 'rgba(0,0,0,0)',
                    camera: { eye: { x: 1.2, y: 1.2, z: 1.2 } }
                },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#ffffff' }
            };

            Plotly.newPlot(containerId, [trace], layout, {responsive: true});
        }

        // Create all visualizations for each miner
        Object.keys(analysisData).forEach(minerKey => {
            create3DSurface(`${minerKey}-hashrate-surface`, `${minerKey.toUpperCase()}: Hashrate Landscape`, minerKey, 'hashrate_th_mean', 'Viridis', 'Hashrate (TH/s)');
            create3DSurface(`${minerKey}-efficiency-surface`, `${minerKey.toUpperCase()}: Efficiency Landscape`, minerKey, 'efficiency_j_th_mean', 'RdYlGn_r', 'Efficiency (J/TH)');
            create3DSurface(`${minerKey}-stability-surface`, `${minerKey.toUpperCase()}: Stability Landscape`, minerKey, 'hashrate_variance_pct', 'RdYlBu_r', 'Stability (±%)');
            createCorrelationPlot(`${minerKey}-correlation`, `${minerKey.toUpperCase()}: Efficiency vs Stability vs Voltage`, minerKey);
        });
    </script>
</body>
</html>"""

        return html_template

    def export_analysis_to_csv(self, analyses: List[Dict], hours: int) -> None:
        """Export analysis results to CSV format"""
        if not self.export_csv:
            return
            
        logger.info("Exporting analysis data to CSV...")
        
        # Prepare data for CSV export
        csv_data = []
        
        for analysis in analyses:
            if 'error' in analysis:
                continue
                
            miner_name = analysis['miner_name']
            recs = analysis['recommendations']
            
            # Add each recommendation type as a row
            for rec_type, rec_data in recs.items():
                csv_data.append({
                    'miner_name': miner_name,
                    'recommendation_type': rec_type,
                    'set_voltage_mv': rec_data['set_voltage_mv'],
                    'frequency_mhz': rec_data['frequency_mhz'],
                    'hashrate_th': rec_data['hashrate_th'],
                    'efficiency_j_th': rec_data['efficiency_j_th'],
                    'variance_pct': rec_data['variance_pct'],
                    'fan_percent': rec_data['fan_percent'],
                    'is_quiet': rec_data['is_quiet'],
                    'actual_voltage_v': rec_data['actual_voltage_v']
                })
        
        if csv_data:
            df = pd.DataFrame(csv_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_file = self.output_dir / f"bitaxe_recommendations_{timestamp}.csv"
            
            df.to_csv(csv_file, index=False)
            logger.info(f"Recommendations exported to: {csv_file}")
        else:
            logger.warning("No data available for CSV export")

    def run_analysis(self, hours: int = 24) -> None:
        """Run complete analysis and generate HTML report"""
        logger.info(f"Starting Bitaxe analysis for last {hours} hours")
        
        # Find latest CSV file
        csv_file = self.find_latest_csv()
        if not csv_file:
            logger.error("No CSV data found - ensure the monitor has been running")
            logger.info("Run the monitor first to collect data: python src/bitaxe_monitor.py")
            return
        
        # Load and filter data
        df = self.load_and_filter_data(csv_file, hours)
        if df.empty:
            logger.error("No data available for analysis")
            logger.info(f"Try increasing --hours parameter or ensure monitor has been running for at least {hours} hours")
            return
        
        # Get unique miners and show summary
        miners = df['miner_name'].unique()
        logger.info(f"Found miners: {list(miners)}")
        
        # Show data summary
        total_records = len(df)
        time_span = df['timestamp'].max() - df['timestamp'].min()
        logger.info(f"Analysis dataset: {total_records} records over {time_span}")
        
        # Analyze each miner with progress reporting
        analyses = []
        for i, miner in enumerate(sorted(miners), 1):
            logger.info(f"Analyzing {miner}... ({i}/{len(miners)})")
            
            analysis = self.analyze_miner_performance(df, miner)
            analyses.append(analysis)
            
            # Show progress summary
            if 'error' not in analysis:
                unique_settings = analysis['unique_settings']
                total_measurements = analysis['total_measurements']
                logger.info(f"  -> {unique_settings} unique settings, {total_measurements} measurements")
            else:
                logger.warning(f"  -> {analysis['error']}")
        
        # Show analysis summary
        successful_analyses = [a for a in analyses if 'error' not in a]
        failed_analyses = [a for a in analyses if 'error' in a]
        
        logger.info(f"Analysis summary: {len(successful_analyses)} successful, {len(failed_analyses)} failed")
        
        if not successful_analyses:
            logger.error("No miners could be analyzed successfully")
            return
        
        # Generate HTML report
        logger.info("Generating comprehensive HTML report...")
        html_content = self.generate_html_report(analyses, hours)
        
        # Export to CSV if requested
        if self.export_csv:
            logger.info("Exporting analysis data to CSV...")
            self.export_analysis_to_csv(analyses, hours)
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"bitaxe_analysis_{timestamp}.html"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Show completion summary
        logger.info("=" * 50)
        logger.info("ANALYSIS COMPLETE!")
        logger.info(f"Report saved to: {output_file}")
        logger.info(f"Open in browser: file://{output_file.absolute()}")
        
        if self.export_csv:
            csv_files = list(self.output_dir.glob("*recommendations*.csv"))
            if csv_files:
                latest_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
                logger.info(f"CSV export saved to: {latest_csv}")
        
        logger.info("=" * 50)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate Bitaxe performance analysis report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Analyze last 24 hours (auto-detect data location)
  %(prog)s --hours 12                   # Analyze last 12 hours  
  %(prog)s --hours 48 --verbose         # Analyze last 48 hours with debug output
  %(prog)s --data-dir ./data --hours 6  # Custom data directory

Data Location:
  The script automatically searches for CSV files in multiple locations:
  1. Current working directory (when run from main project directory)
  2. Parent directory (when run from scripts subdirectory)  
  3. ../data directory (traditional location)
  4. Docker DATA_DIR environment variable (if set)
  
  This makes it work whether you run it from the main directory or scripts directory,
  and whether you're using Docker or running directly.
        """
    )
    
    parser.add_argument('--hours', type=int, default=24, 
                       help='Hours of data to analyze (default: 24)')
    parser.add_argument('--data-dir', type=str, default=None, 
                       help='Data directory path (default: auto-detect)')
    parser.add_argument('--output-dir', type=str, default='../generated_charts', 
                       help='Output directory path (default: ../generated_charts)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose debug output')
    parser.add_argument('--min-measurements', type=int, default=5,
                       help='Minimum measurements per setting combination (default: 5)')
    parser.add_argument('--export-csv', action='store_true',
                       help='Export analysis data to CSV format')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Validate arguments
    if args.hours <= 0:
        logger.error("Hours must be positive")
        sys.exit(1)
        
    if args.min_measurements <= 0:
        logger.error("Minimum measurements must be positive")
        sys.exit(1)
    
    logger.info(f"Starting analysis with settings:")
    logger.info(f"  Hours: {args.hours}")
    logger.info(f"  Data directory: {args.data_dir}")
    logger.info(f"  Output directory: {args.output_dir}")
    logger.info(f"  Min measurements: {args.min_measurements}")
    
    analyzer = BitaxeAnalyzer(args.data_dir, args.output_dir)
    analyzer.min_measurements = args.min_measurements
    analyzer.export_csv = args.export_csv
    analyzer.run_analysis(args.hours)

if __name__ == "__main__":
    main()
