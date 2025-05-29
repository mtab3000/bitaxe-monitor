#!/usr/bin/env python3
"""
Bitaxe CSV Data Visualizer
Generates matplotlib graphs from Multi-Bitaxe Monitor CSV data
Shows hashrate, voltage, and frequency trends over time for each miner
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
import os
import glob
import argparse

class BitaxeVisualizer:
    def __init__(self, csv_file_path):
        """Initialize the visualizer with CSV file path"""
        self.csv_file = csv_file_path
        self.data = None
        self.miners = []
        
    def load_data(self):
        """Load and prepare CSV data"""
        try:
            self.data = pd.read_csv(self.csv_file)
            print(f"✅ Loaded {len(self.data)} data points from {self.csv_file}")
            
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            self.data = self.data[self.data['status'] == 'ONLINE']
            print(f"📊 Found {len(self.data)} online data points")
            
            self.miners = sorted(self.data['miner_name'].unique())
            print(f"🔥 Miners found: {', '.join(self.miners)}")
            
            if len(self.data) == 0:
                print("❌ No online miner data found in CSV file")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error loading CSV file: {e}")
            return False
    
    def create_miner_graphs(self, save_plots=True, show_plots=True):
        """Create individual graphs for each miner"""
        if not self.load_data():
            return
        
        plt.style.use('default')
        
        for miner_name in self.miners:
            miner_data = self.data[self.data['miner_name'] == miner_name].copy()
            
            if len(miner_data) < 2:
                print(f"⚠️  Skipping {miner_name}: Not enough data points")
                continue
            
            miner_data = miner_data.sort_values('timestamp')
            print(f"📊 Creating graph for {miner_name} ({len(miner_data)} data points)")
            
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
            
            # Hashrate graph
            ax1.plot(miner_data['timestamp'], miner_data['hashrate_th'], 
                    color='#2E8B57', linewidth=2, marker='o', markersize=4)
            ax1.set_ylabel('Hashrate (TH/s)', fontweight='bold')
            ax1.grid(True, alpha=0.3)
            hashrate_avg = miner_data['hashrate_th'].mean()
            ax1.axhline(y=hashrate_avg, color='red', linestyle='--', alpha=0.7)
            ax1.text(0.5, -0.15, '⚡ Mining Hashrate Over Time', transform=ax1.transAxes, 
                    ha='center', va='top', fontweight='bold', fontsize=12)
            
            # Voltage graph
            ax2.plot(miner_data['timestamp'], miner_data['voltage_v'], 
                    color='#FF6347', linewidth=2, marker='s', markersize=4)
            ax2.set_ylabel('Core Voltage (V)', fontweight='bold')
            ax2.grid(True, alpha=0.3)
            voltage_avg = miner_data['voltage_v'].mean()
            ax2.axhline(y=voltage_avg, color='red', linestyle='--', alpha=0.7)
            ax2.text(0.5, -0.15, '⚡ Core Voltage Over Time', transform=ax2.transAxes, 
                    ha='center', va='top', fontweight='bold', fontsize=12)
            
            # Frequency graph
            ax3.plot(miner_data['timestamp'], miner_data['frequency_mhz'], 
                    color='#4169E1', linewidth=2, marker='^', markersize=4)
            ax3.set_ylabel('Frequency (MHz)', fontweight='bold')
            ax3.grid(True, alpha=0.3)
            freq_avg = miner_data['frequency_mhz'].mean()
            ax3.axhline(y=freq_avg, color='red', linestyle='--', alpha=0.7)
            ax3.text(0.5, -0.25, '📡 ASIC Frequency Over Time', transform=ax3.transAxes, 
                    ha='center', va='top', fontweight='bold', fontsize=12)
            
            # Format time axis
            for ax in [ax1, ax2, ax3]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
                ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            ax3.set_xlabel('Time (MM/DD HH:MM)', fontweight='bold', fontsize=12)
            fig.suptitle(f'🔥 {miner_name} Performance Trends', fontsize=16, fontweight='bold', y=0.98)
            
            plt.tight_layout()
            plt.subplots_adjust(bottom=0.15)
            
            if save_plots:
                filename = f"{miner_name}_performance_trends.png"
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                print(f"💾 Saved: {filename}")
            
            if show_plots:
                plt.show()
            else:
                plt.close()
    
    def create_combined_overview(self, save_plots=True, show_plots=True):
        """Create overview graph showing all miners"""
        if not self.load_data():
            return
        
        colors = ['#2E8B57', '#FF6347', '#4169E1', '#FFD700', '#8A2BE2', '#FF69B4']
        print(f"📊 Creating combined overview for {len(self.miners)} miners")
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
        
        for i, miner_name in enumerate(self.miners):
            miner_data = self.data[self.data['miner_name'] == miner_name].copy()
            
            if len(miner_data) < 2:
                continue
            
            miner_data = miner_data.sort_values('timestamp')
            color = colors[i % len(colors)]
            
            ax1.plot(miner_data['timestamp'], miner_data['hashrate_th'], 
                    color=color, linewidth=2, marker='o', markersize=3, label=f'{miner_name}', alpha=0.8)
            
            ax2.plot(miner_data['timestamp'], miner_data['voltage_v'], 
                    color=color, linewidth=2, marker='s', markersize=3, label=f'{miner_name}', alpha=0.8)
            
            ax3.plot(miner_data['timestamp'], miner_data['frequency_mhz'], 
                    color=color, linewidth=2, marker='^', markersize=3, label=f'{miner_name}', alpha=0.8)
        
        # Configure axes
        ax1.set_ylabel('Hashrate (TH/s)', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right')
        ax1.text(0.5, -0.15, '⚡ Hashrate Comparison', transform=ax1.transAxes, 
                ha='center', va='top', fontweight='bold', fontsize=12)
        
        ax2.set_ylabel('Core Voltage (V)', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right')
        ax2.text(0.5, -0.15, '⚡ Voltage Comparison', transform=ax2.transAxes, 
                ha='center', va='top', fontweight='bold', fontsize=12)
        
        ax3.set_ylabel('Frequency (MHz)', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc='upper right')
        ax3.text(0.5, -0.25, '📡 Frequency Comparison', transform=ax3.transAxes, 
                ha='center', va='top', fontweight='bold', fontsize=12)
        
        # Format time axis
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        ax3.set_xlabel('Time (MM/DD HH:MM)', fontweight='bold', fontsize=12)
        fig.suptitle('🔥 Multi-Bitaxe Performance Overview', fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.1)
        
        if save_plots:
            filename = "multi_bitaxe_overview.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"💾 Saved: {filename}")
        
        if show_plots:
            plt.show()
        else:
            plt.close()
    
    def create_efficiency_analysis(self, save_plots=True, show_plots=True):
        """Create comprehensive efficiency analysis graphs"""
        if not self.load_data():
            return
        
        print(f"📊 Creating comprehensive efficiency analysis")
        
        fig, axes = plt.subplots(3, 3, figsize=(20, 16))
        colors = ['#2E8B57', '#FF6347', '#4169E1', '#FFD700', '#8A2BE2', '#FF69B4']
        
        for i, miner_name in enumerate(self.miners):
            miner_data = self.data[self.data['miner_name'] == miner_name].copy()
            
            if len(miner_data) < 2:
                continue
            
            miner_data = miner_data.sort_values('timestamp')
            color = colors[i % len(colors)]
            
            # Row 1: Core Performance
            axes[0,0].plot(miner_data['timestamp'], miner_data['efficiency_jth'], 
                    color=color, linewidth=2, marker='o', markersize=3, label=f'{miner_name}', alpha=0.8)
            
            axes[0,1].plot(miner_data['timestamp'], miner_data['power_w'], 
                    color=color, linewidth=2, marker='s', markersize=3, label=f'{miner_name}', alpha=0.8)
            
            axes[0,2].scatter(miner_data['power_w'], miner_data['hashrate_th'], 
                       color=color, alpha=0.6, s=30, label=f'{miner_name}')
            
            # Row 2: Temperature Analysis
            axes[1,0].plot(miner_data['timestamp'], miner_data['temperature_c'], 
                    color=color, linewidth=2, marker='^', markersize=3, label=f'{miner_name}', alpha=0.8)
            
            axes[1,1].plot(miner_data['timestamp'], miner_data['vr_temperature_c'], 
                    color=color, linewidth=2, marker='v', markersize=3, label=f'{miner_name}', alpha=0.8)
            
            axes[1,2].plot(miner_data['timestamp'], miner_data['fan_speed_rpm'], 
                    color=color, linewidth=2, marker='d', markersize=3, label=f'{miner_name}', alpha=0.8)
            
            # Row 3: Advanced Analysis
            axes[2,0].scatter(miner_data['temperature_c'], miner_data['efficiency_jth'], 
                       color=color, alpha=0.6, s=30, label=f'{miner_name}')
            
            axes[2,1].scatter(miner_data['voltage_v'], miner_data['frequency_mhz'], 
                       color=color, alpha=0.6, s=30, label=f'{miner_name}')
            
            axes[2,2].scatter(miner_data['temperature_c'], miner_data['power_w'], 
                       color=color, alpha=0.6, s=30, label=f'{miner_name}')
        
        # Configure all axes
        titles = [
            ['⚙️ Power Efficiency Over Time', '🔌 Power Consumption Over Time', '⚡ Hashrate vs Power'],
            ['🌡️ ASIC Temperature Over Time', '🌡️ VR Temperature Over Time', '💨 Fan Speed Over Time'],
            ['🔥 Efficiency vs Temperature', '⚡ Voltage vs Frequency', '🔌 Power vs Temperature']
        ]
        
        ylabels = [
            ['Efficiency (J/TH)', 'Power (W)', 'Hashrate (TH/s)'],
            ['ASIC Temp (°C)', 'VR Temp (°C)', 'Fan Speed (RPM)'],
            ['Efficiency (J/TH)', 'Frequency (MHz)', 'Power (W)']
        ]
        
        xlabels = [
            ['', '', 'Power (W)'],
            ['', '', ''],
            ['ASIC Temp (°C)', 'Core Voltage (V)', 'ASIC Temp (°C)']
        ]
        
        for i in range(3):
            for j in range(3):
                ax = axes[i,j]
                ax.set_ylabel(ylabels[i][j], fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.legend(fontsize=8)
                ax.text(0.5, -0.12, titles[i][j], transform=ax.transAxes, 
                       ha='center', va='top', fontweight='bold', fontsize=10)
                
                if xlabels[i][j]:
                    ax.set_xlabel(xlabels[i][j], fontweight='bold')
        
        # Format time axes
        time_axes = [axes[0,0], axes[0,1], axes[1,0], axes[1,1], axes[1,2]]
        for ax in time_axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=60))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=8)
        
        # Add time labels to bottom time-based graphs
        axes[1,0].set_xlabel('Time (MM/DD HH:MM)', fontweight='bold', fontsize=10)
        axes[1,1].set_xlabel('Time (MM/DD HH:MM)', fontweight='bold', fontsize=10)
        axes[1,2].set_xlabel('Time (MM/DD HH:MM)', fontweight='bold', fontsize=10)
        
        fig.suptitle('📊 Comprehensive Mining Performance Analysis', fontsize=18, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.92, bottom=0.08, hspace=0.35, wspace=0.3)
        
        if save_plots:
            filename = "bitaxe_comprehensive_analysis.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"💾 Saved: {filename}")
        
        if show_plots:
            plt.show()
        else:
            plt.close()
    
    def create_optimization_charts(self, save_plots=True, show_plots=True):
        """Create optimization recommendation charts"""
        if not self.load_data():
            return
        
        print(f"🎯 Creating optimization recommendation charts")
        self.create_hashrate_optimization_chart(save_plots, show_plots)
        self.create_efficiency_optimization_chart(save_plots, show_plots)
        
    def create_hashrate_optimization_chart(self, save_plots=True, show_plots=True):
        """Create chart showing optimal settings for maximum hashrate"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('🚀 MAXIMUM HASHRATE OPTIMIZATION SETTINGS', fontsize=16, fontweight='bold', y=0.98)
        
        colors = ['#2E8B57', '#FF6347', '#4169E1', '#FFD700', '#8A2BE2', '#FF69B4']
        hashrate_data = {}
        
        for i, miner_name in enumerate(self.miners):
            miner_data = self.data[self.data['miner_name'] == miner_name].copy()
            
            if len(miner_data) < 5:
                continue
            
            top_hashrate = miner_data.nlargest(5, 'hashrate_th')
            hashrate_data[miner_name] = {
                'data': top_hashrate,
                'color': colors[i % len(colors)]
            }
        
        # Create scatter plots
        for miner_name, info in hashrate_data.items():
            data = info['data']
            best_point = data.iloc[0]
            
            # Frequency vs Hashrate
            axes[0,0].scatter(data['frequency_mhz'], data['hashrate_th'], 
                       color=info['color'], s=100, alpha=0.8, label=f'{miner_name}')
            axes[0,0].scatter(best_point['frequency_mhz'], best_point['hashrate_th'], 
                       color=info['color'], s=200, marker='*', edgecolors='gold', linewidth=2)
            
            # Voltage vs Hashrate
            axes[0,1].scatter(data['voltage_v'], data['hashrate_th'], 
                       color=info['color'], s=100, alpha=0.8, label=f'{miner_name}')
            axes[0,1].scatter(best_point['voltage_v'], best_point['hashrate_th'], 
                       color=info['color'], s=200, marker='*', edgecolors='gold', linewidth=2)
            
            # Temperature vs Hashrate
            axes[1,0].scatter(data['temperature_c'], data['hashrate_th'], 
                       color=info['color'], s=100, alpha=0.8, label=f'{miner_name}')
            axes[1,0].scatter(best_point['temperature_c'], best_point['hashrate_th'], 
                       color=info['color'], s=200, marker='*', edgecolors='gold', linewidth=2)
        
        # Configure axes
        axes[0,0].set_xlabel('Frequency (MHz)', fontweight='bold')
        axes[0,0].set_ylabel('Hashrate (TH/s)', fontweight='bold')
        axes[0,0].grid(True, alpha=0.3)
        axes[0,0].legend()
        axes[0,0].text(0.5, -0.12, '📡 Optimal Frequency for Max Hashrate', transform=axes[0,0].transAxes, 
                ha='center', va='top', fontweight='bold', fontsize=11)
        
        axes[0,1].set_xlabel('Core Voltage (V)', fontweight='bold')
        axes[0,1].set_ylabel('Hashrate (TH/s)', fontweight='bold')
        axes[0,1].grid(True, alpha=0.3)
        axes[0,1].legend()
        axes[0,1].text(0.5, -0.12, '⚡ Optimal Voltage for Max Hashrate', transform=axes[0,1].transAxes, 
                ha='center', va='top', fontweight='bold', fontsize=11)
        
        axes[1,0].set_xlabel('ASIC Temperature (°C)', fontweight='bold')
        axes[1,0].set_ylabel('Hashrate (TH/s)', fontweight='bold')
        axes[1,0].grid(True, alpha=0.3)
        axes[1,0].legend()
        axes[1,0].text(0.5, -0.12, '🌡️ Temperature vs Max Hashrate', transform=axes[1,0].transAxes, 
                ha='center', va='top', fontweight='bold', fontsize=11)
        
        # Settings summary
        axes[1,1].axis('off')
        summary_text = "🎯 TOP HASHRATE SETTINGS SUMMARY:\n\n"
        for miner_name, info in hashrate_data.items():
            best = info['data'].iloc[0]
            summary_text += f"🔥 {miner_name}:\n"
            summary_text += f"   Max: {best['hashrate_th']:.3f} TH/s\n"
            summary_text += f"   Freq: {best['frequency_mhz']:.0f} MHz\n"
            summary_text += f"   Voltage: {best['voltage_v']:.3f} V\n"
            summary_text += f"   Temp: {best['temperature_c']:.1f}°C\n\n"
        
        axes[1,1].text(0.05, 0.95, summary_text, transform=axes[1,1].transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgreen", alpha=0.8))
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.93, hspace=0.3, wspace=0.3)
        
        if save_plots:
            filename = "bitaxe_hashrate_optimization.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"💾 Saved: {filename}")
        
        if show_plots:
            plt.show()
        else:
            plt.close()
    
    def create_efficiency_optimization_chart(self, save_plots=True, show_plots=True):
        """Create chart showing optimal settings for maximum efficiency"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('⚙️ MAXIMUM EFFICIENCY OPTIMIZATION SETTINGS', fontsize=16, fontweight='bold', y=0.98)
        
        colors = ['#2E8B57', '#FF6347', '#4169E1', '#FFD700', '#8A2BE2', '#FF69B4']
        efficiency_data = {}
        
        for i, miner_name in enumerate(self.miners):
            miner_data = self.data[self.data['miner_name'] == miner_name].copy()
            
            if len(miner_data) < 5:
                continue
            
            top_efficiency = miner_data.nsmallest(5, 'efficiency_jth')
            efficiency_data[miner_name] = {
                'data': top_efficiency,
                'color': colors[i % len(colors)]
            }
        
        # Create scatter plots
        for miner_name, info in efficiency_data.items():
            data = info['data']
            best_point = data.iloc[0]
            
            # Frequency vs Efficiency
            axes[0,0].scatter(data['frequency_mhz'], data['efficiency_jth'], 
                       color=info['color'], s=100, alpha=0.8, label=f'{miner_name}')
            axes[0,0].scatter(best_point['frequency_mhz'], best_point['efficiency_jth'], 
                       color=info['color'], s=200, marker='*', edgecolors='gold', linewidth=2)
            
            # Voltage vs Efficiency
            axes[0,1].scatter(data['voltage_v'], data['efficiency_jth'], 
                       color=info['color'], s=100, alpha=0.8, label=f'{miner_name}')
            axes[0,1].scatter(best_point['voltage_v'], best_point['efficiency_jth'], 
                       color=info['color'], s=200, marker='*', edgecolors='gold', linewidth=2)
            
            # Temperature vs Efficiency
            axes[1,0].scatter(data['temperature_c'], data['efficiency_jth'], 
                       color=info['color'], s=100, alpha=0.8, label=f'{miner_name}')
            axes[1,0].scatter(best_point['temperature_c'], best_point['efficiency_jth'], 
                       color=info['color'], s=200, marker='*', edgecolors='gold', linewidth=2)
        
        # Configure axes
        axes[0,0].set_xlabel('Frequency (MHz)', fontweight='bold')
        axes[0,0].set_ylabel('Efficiency (J/TH)', fontweight='bold')
        axes[0,0].grid(True, alpha=0.3)
        axes[0,0].legend()
        axes[0,0].text(0.5, -0.12, '📡 Optimal Frequency for Max Efficiency', transform=axes[0,0].transAxes, 
                ha='center', va='top', fontweight='bold', fontsize=11)
        
        axes[0,1].set_xlabel('Core Voltage (V)', fontweight='bold')
        axes[0,1].set_ylabel('Efficiency (J/TH)', fontweight='bold')
        axes[0,1].grid(True, alpha=0.3)
        axes[0,1].legend()
        axes[0,1].text(0.5, -0.12, '⚡ Optimal Voltage for Max Efficiency', transform=axes[0,1].transAxes, 
                ha='center', va='top', fontweight='bold', fontsize=11)
        
        axes[1,0].set_xlabel('ASIC Temperature (°C)', fontweight='bold')
        axes[1,0].set_ylabel('Efficiency (J/TH)', fontweight='bold')
        axes[1,0].grid(True, alpha=0.3)
        axes[1,0].legend()
        axes[1,0].text(0.5, -0.12, '🌡️ Temperature vs Max Efficiency', transform=axes[1,0].transAxes, 
                ha='center', va='top', fontweight='bold', fontsize=11)
        
        # Settings summary
        axes[1,1].axis('off')
        summary_text = "🎯 TOP EFFICIENCY SETTINGS SUMMARY:\n\n"
        for miner_name, info in efficiency_data.items():
            best = info['data'].iloc[0]
            summary_text += f"⚙️ {miner_name}:\n"
            summary_text += f"   Best: {best['efficiency_jth']:.2f} J/TH\n"
            summary_text += f"   Freq: {best['frequency_mhz']:.0f} MHz\n"
            summary_text += f"   Voltage: {best['voltage_v']:.3f} V\n"
            summary_text += f"   Temp: {best['temperature_c']:.1f}°C\n\n"
        
        axes[1,1].text(0.05, 0.95, summary_text, transform=axes[1,1].transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.93, hspace=0.3, wspace=0.3)
        
        if save_plots:
            filename = "bitaxe_efficiency_optimization.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"💾 Saved: {filename}")
        
        if show_plots:
            plt.show()
        else:
            plt.close()

def find_latest_csv():
    """Find the most recent CSV file in current directory"""
    csv_files = glob.glob("multi_bitaxe_kpis_*.csv")
    if not csv_files:
        return None
    
    csv_files.sort(key=os.path.getmtime, reverse=True)
    return csv_files[0]

def main():
    parser = argparse.ArgumentParser(description='Visualize Bitaxe CSV data')
    parser.add_argument('--csv', '-f', type=str, help='CSV file path (defaults to most recent)')
    parser.add_argument('--no-show', action='store_true', help='Don\'t display plots on screen')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save plots as files')
    parser.add_argument('--individual-only', action='store_true', help='Only create individual miner graphs')
    parser.add_argument('--overview-only', action='store_true', help='Only create overview graphs')
    
    args = parser.parse_args()
    
    # Find CSV file
    if args.csv:
        csv_file = args.csv
    else:
        csv_file = find_latest_csv()
        if not csv_file:
            print("❌ No CSV files found. Please specify a file with --csv option.")
            print("💡 Run the Multi-Bitaxe Monitor first to generate CSV data.")
            return
        else:
            print(f"📁 Using most recent CSV file: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    # Create visualizer
    visualizer = BitaxeVisualizer(csv_file)
    
    show_plots = not args.no_show
    save_plots = not args.no_save
    
    print(f"🎨 Starting visualization...")
    print(f"📊 Show plots: {show_plots}")
    print(f"💾 Save plots: {save_plots}")
    
    # Generate graphs based on options
    if not args.overview_only:
        print("\n📈 Creating individual miner graphs...")
        visualizer.create_miner_graphs(save_plots=save_plots, show_plots=show_plots)

    if not args.individual_only:
        print("\n📊 Creating overview graphs...")
        visualizer.create_combined_overview(save_plots=save_plots, show_plots=show_plots)
        
        print("\n⚙️ Creating efficiency analysis...")
        visualizer.create_efficiency_analysis(save_plots=save_plots, show_plots=show_plots)
        
        print("\n🎯 Creating optimization charts...")
        visualizer.create_optimization_charts(save_plots=save_plots, show_plots=show_plots)
    
    print("\n✅ Visualization complete!")
    if save_plots:
        print("📁 Check current directory for saved PNG files:")
        print("   - Individual miner graphs: [MinerName]_performance_trends.png")
        print("   - Overview comparison: multi_bitaxe_overview.png")
        print("   - Performance analysis: bitaxe_comprehensive_analysis.png")
        print("   - Hashrate optimization: bitaxe_hashrate_optimization.png")  
        print("   - Efficiency optimization: bitaxe_efficiency_optimization.png")

if __name__ == "__main__":
    main()