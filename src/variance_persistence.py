#!/usr/bin/env python3
"""
Enhanced Variance Data Persistence System

This module provides specialized storage and analysis for variance tracking data,
focusing on positive and negative deviations from expected hashrate baselines.

Features:
- Dedicated variance metrics storage
- Long-term variance trend analysis
- Compressed historical data for extended storage
- Performance analytics for variance patterns

Author: mtab3000
License: MIT
"""

import csv
import json
import os
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class VarianceDataStore:
    """Enhanced storage system for variance tracking data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.csv_filename = os.path.join(data_dir, "variance_tracking.csv")
        self.db_filename = os.path.join(data_dir, "variance_analytics.db")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize storage systems
        self._setup_csv()
        self._setup_database()
    
    def _setup_csv(self):
        """Setup CSV file for variance data"""
        if not os.path.exists(self.csv_filename):
            headers = [
                'timestamp', 'miner_name', 'window_seconds',
                'expected_hashrate_gh', 'actual_hashrate_gh', 'deviation_gh',
                'positive_variance', 'negative_variance', 'avg_deviation',
                'sample_count', 'positive_count', 'negative_count',
                'variance_ratio', 'stability_score'
            ]
            
            with open(self.csv_filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def _setup_database(self):
        """Setup SQLite database for analytics"""
        with sqlite3.connect(self.db_filename) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS variance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    miner_name TEXT,
                    window_seconds INTEGER,
                    expected_hashrate_gh REAL,
                    actual_hashrate_gh REAL,
                    deviation_gh REAL,
                    positive_variance REAL,
                    negative_variance REAL,
                    avg_deviation REAL,
                    sample_count INTEGER,
                    positive_count INTEGER,
                    negative_count INTEGER,
                    variance_ratio REAL,
                    stability_score REAL
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_variance_timestamp ON variance_metrics (timestamp)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_variance_miner ON variance_metrics (miner_name)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_variance_window ON variance_metrics (window_seconds)
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS variance_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    miner_name TEXT,
                    window_seconds INTEGER,
                    avg_positive_variance REAL,
                    avg_negative_variance REAL,
                    max_positive_deviation REAL,
                    max_negative_deviation REAL,
                    stability_score REAL,
                    efficiency_correlation REAL,
                    UNIQUE(date, miner_name, window_seconds)
                )
            ''')
            
            conn.commit()
    
    def log_variance_data(self, timestamp: datetime, miner_name: str, 
                         directional_variance_data: Dict, expected_hashrate: float, 
                         actual_hashrate: float):
        """Log comprehensive variance data for all time windows"""
        
        for window_seconds in [60, 300, 600]:
            window_key = f"{window_seconds}s"
            variance_data = directional_variance_data.get(window_key, {})
            
            if not variance_data or variance_data.get('total_samples', 0) < 2:
                continue
            
            # Calculate additional metrics
            deviation = actual_hashrate - expected_hashrate
            positive_variance = variance_data.get('positive_variance')
            negative_variance = variance_data.get('negative_variance')
            avg_deviation = variance_data.get('avg_deviation', 0)
            sample_count = variance_data.get('total_samples', 0)
            positive_count = variance_data.get('positive_count', 0)
            negative_count = variance_data.get('negative_count', 0)
            
            # Calculate variance ratio (positive vs negative variance)
            variance_ratio = 0
            if positive_variance and negative_variance:
                variance_ratio = positive_variance / negative_variance
            elif positive_variance:
                variance_ratio = float('inf')
            elif negative_variance:
                variance_ratio = 0
            
            # Calculate stability score (0-100, higher is more stable)
            stability_score = self._calculate_stability_score(
                positive_variance, negative_variance, avg_deviation, expected_hashrate
            )
            
            # Log to CSV
            self._log_to_csv(
                timestamp, miner_name, window_seconds, expected_hashrate, 
                actual_hashrate, deviation, positive_variance, negative_variance,
                avg_deviation, sample_count, positive_count, negative_count,
                variance_ratio, stability_score
            )
            
            # Log to database
            self._log_to_database(
                timestamp, miner_name, window_seconds, expected_hashrate,
                actual_hashrate, deviation, positive_variance, negative_variance,
                avg_deviation, sample_count, positive_count, negative_count,
                variance_ratio, stability_score
            )
    
    def _calculate_stability_score(self, positive_var: Optional[float], 
                                 negative_var: Optional[float], 
                                 avg_deviation: float, 
                                 expected_hashrate: float) -> float:
        """Calculate stability score (0-100, higher is more stable)"""
        if expected_hashrate <= 0:
            return 0
        
        # Base score on deviation percentage
        deviation_pct = abs(avg_deviation) / expected_hashrate * 100
        base_score = max(0, 100 - deviation_pct * 2)  # Penalize high deviation
        
        # Adjust for variance levels
        if positive_var and negative_var:
            avg_variance = (positive_var + negative_var) / 2
            variance_pct = avg_variance / expected_hashrate * 100
            variance_penalty = min(variance_pct, 50)  # Cap penalty at 50 points
            base_score = max(0, base_score - variance_penalty)
        
        return round(base_score, 1)
    
    def _log_to_csv(self, timestamp: datetime, miner_name: str, window_seconds: int,
                    expected_hashrate: float, actual_hashrate: float, deviation: float,
                    positive_variance: Optional[float], negative_variance: Optional[float],
                    avg_deviation: float, sample_count: int, positive_count: int,
                    negative_count: int, variance_ratio: float, stability_score: float):
        """Log variance data to CSV file"""
        
        with open(self.csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp.isoformat(),
                miner_name,
                window_seconds,
                round(expected_hashrate, 2),
                round(actual_hashrate, 2),
                round(deviation, 2),
                round(positive_variance, 2) if positive_variance else '',
                round(negative_variance, 2) if negative_variance else '',
                round(avg_deviation, 2),
                sample_count,
                positive_count,
                negative_count,
                round(variance_ratio, 2) if variance_ratio != float('inf') else 'INF',
                stability_score
            ])
    
    def _log_to_database(self, timestamp: datetime, miner_name: str, window_seconds: int,
                        expected_hashrate: float, actual_hashrate: float, deviation: float,
                        positive_variance: Optional[float], negative_variance: Optional[float],
                        avg_deviation: float, sample_count: int, positive_count: int,
                        negative_count: int, variance_ratio: float, stability_score: float):
        """Log variance data to SQLite database"""
        
        with sqlite3.connect(self.db_filename) as conn:
            conn.execute('''
                INSERT INTO variance_metrics (
                    timestamp, miner_name, window_seconds, expected_hashrate_gh,
                    actual_hashrate_gh, deviation_gh, positive_variance, negative_variance,
                    avg_deviation, sample_count, positive_count, negative_count,
                    variance_ratio, stability_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp, miner_name, window_seconds, expected_hashrate,
                actual_hashrate, deviation, positive_variance, negative_variance,
                avg_deviation, sample_count, positive_count, negative_count,
                variance_ratio, stability_score
            ))
            conn.commit()
    
    def get_variance_analytics(self, miner_name: str, days: int = 7) -> Dict:
        """Get variance analytics for a miner over specified days"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_filename) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get variance trends
            cursor = conn.execute('''
                SELECT window_seconds, 
                       AVG(positive_variance) as avg_pos_var,
                       AVG(negative_variance) as avg_neg_var,
                       AVG(stability_score) as avg_stability,
                       COUNT(*) as sample_count
                FROM variance_metrics 
                WHERE miner_name = ? AND timestamp >= ?
                GROUP BY window_seconds
                ORDER BY window_seconds
            ''', (miner_name, cutoff_date))
            
            trends = [dict(row) for row in cursor.fetchall()]
            
            # Get worst variance periods
            cursor = conn.execute('''
                SELECT timestamp, window_seconds, stability_score, deviation_gh
                FROM variance_metrics 
                WHERE miner_name = ? AND timestamp >= ?
                ORDER BY stability_score ASC
                LIMIT 10
            ''', (miner_name, cutoff_date))
            
            worst_periods = [dict(row) for row in cursor.fetchall()]
            
            # Get best stability periods
            cursor = conn.execute('''
                SELECT timestamp, window_seconds, stability_score, deviation_gh
                FROM variance_metrics 
                WHERE miner_name = ? AND timestamp >= ?
                ORDER BY stability_score DESC
                LIMIT 10
            ''', (miner_name, cutoff_date))
            
            best_periods = [dict(row) for row in cursor.fetchall()]
            
            return {
                'miner_name': miner_name,
                'analysis_period_days': days,
                'variance_trends': trends,
                'worst_stability_periods': worst_periods,
                'best_stability_periods': best_periods
            }
    
    def generate_daily_summary(self, target_date: datetime = None):
        """Generate daily variance summary for all miners"""
        
        if target_date is None:
            target_date = datetime.now().date()
        
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        
        with sqlite3.connect(self.db_filename) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute('''
                SELECT miner_name, window_seconds,
                       AVG(positive_variance) as avg_positive_variance,
                       AVG(negative_variance) as avg_negative_variance,
                       MAX(ABS(deviation_gh)) as max_deviation,
                       AVG(stability_score) as avg_stability_score,
                       COUNT(*) as measurement_count
                FROM variance_metrics 
                WHERE timestamp >= ? AND timestamp < ?
                GROUP BY miner_name, window_seconds
            ''', (start_time, end_time))
            
            results = [dict(row) for row in cursor.fetchall()]
            
            # Insert daily summary
            for result in results:
                conn.execute('''
                    INSERT OR REPLACE INTO variance_summary (
                        date, miner_name, window_seconds, avg_positive_variance,
                        avg_negative_variance, max_positive_deviation, max_negative_deviation,
                        stability_score, efficiency_correlation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    target_date, result['miner_name'], result['window_seconds'],
                    result['avg_positive_variance'], result['avg_negative_variance'],
                    result['max_deviation'], result['max_deviation'],  # Simplified for now
                    result['avg_stability_score'], 0  # Correlation TBD
                ))
            
            conn.commit()
            
            return {
                'date': target_date.isoformat(),
                'summaries_generated': len(results),
                'miners_processed': len(set(r['miner_name'] for r in results))
            }
    
    def export_variance_report(self, miner_name: str, days: int = 30) -> str:
        """Export comprehensive variance report for a miner"""
        
        analytics = self.get_variance_analytics(miner_name, days)
        
        report_lines = [
            f"Variance Analysis Report for {miner_name}",
            f"Analysis Period: {days} days",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            "Variance Trends by Time Window:",
        ]
        
        for trend in analytics['variance_trends']:
            report_lines.extend([
                f"  {trend['window_seconds']}s window:",
                f"    Average Positive Variance: {trend['avg_pos_var']:.2f} GH/s" if trend['avg_pos_var'] else "    Average Positive Variance: N/A",
                f"    Average Negative Variance: {trend['avg_neg_var']:.2f} GH/s" if trend['avg_neg_var'] else "    Average Negative Variance: N/A", 
                f"    Average Stability Score: {trend['avg_stability']:.1f}/100",
                f"    Sample Count: {trend['sample_count']}",
                ""
            ])
        
        report_lines.extend([
            "Worst Stability Periods:",
            "  Timestamp                | Window | Score | Deviation"
        ])
        
        for period in analytics['worst_stability_periods'][:5]:
            ts = datetime.fromisoformat(period['timestamp']).strftime('%Y-%m-%d %H:%M')
            report_lines.append(f"  {ts} | {period['window_seconds']:3d}s  | {period['stability_score']:5.1f} | {period['deviation_gh']:+6.1f} GH/s")
        
        report_content = "\n".join(report_lines)
        
        # Save report to file
        report_filename = f"variance_report_{miner_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = os.path.join(self.data_dir, report_filename)
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        return report_path

class VarianceTracker:
    """Integration layer for variance tracking with main monitor"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_store = VarianceDataStore(data_dir)
        self.last_daily_summary = None
    
    def log_miner_variance(self, timestamp: datetime, miner_name: str, 
                          variance_60s: Dict, variance_300s: Dict, variance_600s: Dict,
                          expected_hashrate: float, actual_hashrate: float):
        """Log variance data for all time windows"""
        
        directional_variance_data = {
            '60s': variance_60s,
            '300s': variance_300s,
            '600s': variance_600s
        }
        
        self.data_store.log_variance_data(
            timestamp, miner_name, directional_variance_data,
            expected_hashrate, actual_hashrate
        )
        
        # Generate daily summary if it's a new day
        current_date = timestamp.date()
        if self.last_daily_summary != current_date:
            try:
                self.data_store.generate_daily_summary(current_date)
                self.last_daily_summary = current_date
                logger.info(f"Generated daily variance summary for {current_date}")
            except Exception as e:
                logger.error(f"Failed to generate daily summary: {e}")
    
    def get_miner_analytics(self, miner_name: str, days: int = 7) -> Dict:
        """Get analytics for a specific miner"""
        return self.data_store.get_variance_analytics(miner_name, days)
    
    def export_miner_report(self, miner_name: str, days: int = 30) -> str:
        """Export detailed report for a miner"""
        return self.data_store.export_variance_report(miner_name, days)
