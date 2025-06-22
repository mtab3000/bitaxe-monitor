"""
Enhanced Variance Monitoring Dashboard

This script adds enhanced variance analytics display to the web interface.
It creates interactive charts and tables for monitoring variance trends.
"""

def add_variance_dashboard_html():
    """Returns HTML snippet for enhanced variance dashboard"""
    return '''
        <!-- Enhanced Variance Analytics Dashboard -->
        <div id="varianceAnalytics" style="display: none; margin-top: 30px;">
            <h2>Enhanced Variance Analytics</h2>
            
            <div class="variance-controls">
                <button onclick="toggleVarianceView('analytics')" class="variance-btn active" id="analyticsBtn">Analytics</button>
                <button onclick="toggleVarianceView('trends')" class="variance-btn" id="trendsBtn">Trends</button>
                <button onclick="toggleVarianceView('reports')" class="variance-btn" id="reportsBtn">Reports</button>
            </div>
            
            <!-- Analytics View -->
            <div id="analyticsView" class="variance-view">
                <div class="variance-summary-grid" id="varianceSummaryGrid">
                    <!-- Summary cards will be inserted here -->
                </div>
            </div>
            
            <!-- Trends View -->
            <div id="trendsView" class="variance-view" style="display: none;">
                <div class="trend-charts">
                    <div class="chart-container">
                        <div class="chart-title">Stability Score Trends (7 days)</div>
                        <canvas id="stabilityTrendChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">Variance Distribution</div>
                        <canvas id="varianceDistributionChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Reports View -->
            <div id="reportsView" class="variance-view" style="display: none;">
                <div class="report-controls">
                    <select id="reportMinerSelect">
                        <option value="">Select Miner</option>
                    </select>
                    <select id="reportDaysSelect">
                        <option value="7">7 Days</option>
                        <option value="14">14 Days</option>
                        <option value="30" selected>30 Days</option>
                    </select>
                    <button onclick="generateVarianceReport()" class="variance-btn">Generate Report</button>
                </div>
                <div id="reportDisplay" class="report-display">
                    <p>Select a miner and click "Generate Report" to view detailed variance analysis.</p>
                </div>
            </div>
        </div>
        
        <!-- Toggle button for variance analytics -->
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="toggleVarianceAnalytics()" class="view-toggle" id="varianceToggle">
                Show Enhanced Variance Analytics
            </button>
        </div>
        
        <style>
        .variance-controls {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
            gap: 10px;
        }
        
        .variance-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .variance-btn.active {
            background: #007bff;
        }
        
        .variance-btn:hover {
            opacity: 0.9;
        }
        
        .variance-summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .variance-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #007bff;
        }
        
        .variance-card.warning {
            border-left-color: #ffc107;
        }
        
        .variance-card.danger {
            border-left-color: #dc3545;
        }
        
        .variance-card.success {
            border-left-color: #28a745;
        }
        
        .variance-metric {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 4px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .variance-metric:last-child {
            border-bottom: none;
        }
        
        .variance-label {
            font-weight: 500;
            color: #666;
        }
        
        .variance-value {
            font-weight: bold;
        }
        
        .variance-value.good {
            color: #28a745;
        }
        
        .variance-value.warning {
            color: #ffc107;
        }
        
        .variance-value.danger {
            color: #dc3545;
        }
        
        .trend-charts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .report-controls {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .report-controls select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .report-display {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            min-height: 300px;
            white-space: pre-wrap;
            font-family: monospace;
        }
        
        @media (max-width: 768px) {
            .trend-charts {
                grid-template-columns: 1fr;
            }
            .variance-summary-grid {
                grid-template-columns: 1fr;
            }
            .report-controls {
                flex-direction: column;
                align-items: stretch;
            }
        }
        </style>
        
        <script>
        let varianceAnalyticsVisible = false;
        let currentVarianceView = 'analytics';
        
        function toggleVarianceAnalytics() {
            const analyticsDiv = document.getElementById('varianceAnalytics');
            const toggleBtn = document.getElementById('varianceToggle');
            
            varianceAnalyticsVisible = !varianceAnalyticsVisible;
            
            if (varianceAnalyticsVisible) {
                analyticsDiv.style.display = 'block';
                toggleBtn.textContent = 'Hide Enhanced Variance Analytics';
                loadVarianceData();
            } else {
                analyticsDiv.style.display = 'none';
                toggleBtn.textContent = 'Show Enhanced Variance Analytics';
            }
        }
        
        function toggleVarianceView(view) {
            // Hide all views
            document.querySelectorAll('.variance-view').forEach(v => v.style.display = 'none');
            document.querySelectorAll('.variance-btn').forEach(b => b.classList.remove('active'));
            
            // Show selected view
            document.getElementById(view + 'View').style.display = 'block';
            document.getElementById(view + 'Btn').classList.add('active');
            
            currentVarianceView = view;
            
            if (view === 'analytics') {
                loadVarianceData();
            } else if (view === 'trends') {
                loadTrendCharts();
            } else if (view === 'reports') {
                populateReportMinerSelect();
            }
        }
        
        function loadVarianceData() {
            fetch('/api/variance/summary')
                .then(response => response.json())
                .then(data => {
                    displayVarianceSummary(data.miner_summaries);
                })
                .catch(error => {
                    console.error('Error loading variance data:', error);
                });
        }
        
        function displayVarianceSummary(summaries) {
            const grid = document.getElementById('varianceSummaryGrid');
            let html = '';
            
            for (const [minerName, data] of Object.entries(summaries)) {
                let cardClass = 'variance-card';
                if (data.stability_score >= 80) cardClass += ' success';
                else if (data.stability_score >= 60) cardClass += ' warning';
                else cardClass += ' danger';
                
                html += `
                    <div class="${cardClass}">
                        <h4>${minerName}</h4>
                        <div class="variance-metric">
                            <span class="variance-label">Stability Score:</span>
                            <span class="variance-value ${getStabilityClass(data.stability_score)}">${data.stability_score}/100</span>
                        </div>
                        <div class="variance-metric">
                            <span class="variance-label">Efficiency:</span>
                            <span class="variance-value ${getEfficiencyClass(data.efficiency_pct)}">${data.efficiency_pct}%</span>
                        </div>
                        <div class="variance-metric">
                            <span class="variance-label">Current Deviation:</span>
                            <span class="variance-value">${data.current_deviation > 0 ? '+' : ''}${data.current_deviation} GH/s</span>
                        </div>
                        <div class="variance-metric">
                            <span class="variance-label">Variance (60s):</span>
                            <span class="variance-value">${data.variance_60s} GH/s</span>
                        </div>
                        <div class="variance-metric">
                            <span class="variance-label">Variance (300s):</span>
                            <span class="variance-value">${data.variance_300s} GH/s</span>
                        </div>
                        <div class="variance-metric">
                            <span class="variance-label">Variance (600s):</span>
                            <span class="variance-value">${data.variance_600s} GH/s</span>
                        </div>
                    </div>
                `;
            }
            
            grid.innerHTML = html;
        }
        
        function getStabilityClass(score) {
            if (score >= 80) return 'good';
            if (score >= 60) return 'warning';
            return 'danger';
        }
        
        function loadTrendCharts() {
            // Placeholder for trend chart implementation
            console.log('Loading trend charts...');
        }
        
        function populateReportMinerSelect() {
            const select = document.getElementById('reportMinerSelect');
            
            // Get current miners from the main data
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    select.innerHTML = '<option value="">Select Miner</option>';
                    data.miners.forEach(miner => {
                        if (miner.status === 'ONLINE') {
                            select.innerHTML += `<option value="${miner.miner_name}">${miner.miner_name}</option>`;
                        }
                    });
                });
        }
        
        function generateVarianceReport() {
            const minerSelect = document.getElementById('reportMinerSelect');
            const daysSelect = document.getElementById('reportDaysSelect');
            const reportDisplay = document.getElementById('reportDisplay');
            
            const minerName = minerSelect.value;
            const days = daysSelect.value;
            
            if (!minerName) {
                alert('Please select a miner');
                return;
            }
            
            reportDisplay.innerHTML = 'Generating report...';
            
            fetch(`/api/variance/analytics/${minerName}?days=${days}`)
                .then(response => response.json())
                .then(data => {
                    displayVarianceReport(data);
                })
                .catch(error => {
                    reportDisplay.innerHTML = 'Error generating report: ' + error;
                });
        }
        
        function displayVarianceReport(data) {
            const reportDisplay = document.getElementById('reportDisplay');
            
            let report = `Variance Analysis Report for ${data.miner_name}\n`;
            report += `Analysis Period: ${data.analysis_period_days} days\n`;
            report += `Generated: ${new Date().toLocaleString()}\n`;
            report += '='.repeat(60) + '\n\n';
            
            report += 'Variance Trends by Time Window:\n';
            data.variance_trends.forEach(trend => {
                report += `  ${trend.window_seconds}s window:\n`;
                report += `    Average Positive Variance: ${trend.avg_pos_var ? trend.avg_pos_var.toFixed(2) + ' GH/s' : 'N/A'}\n`;
                report += `    Average Negative Variance: ${trend.avg_neg_var ? trend.avg_neg_var.toFixed(2) + ' GH/s' : 'N/A'}\n`;
                report += `    Average Stability Score: ${trend.avg_stability ? trend.avg_stability.toFixed(1) + '/100' : 'N/A'}\n`;
                report += `    Sample Count: ${trend.sample_count}\n\n`;
            });
            
            if (data.worst_stability_periods && data.worst_stability_periods.length > 0) {
                report += 'Worst Stability Periods:\n';
                report += '  Timestamp           | Window | Score | Deviation\n';
                data.worst_stability_periods.slice(0, 5).forEach(period => {
                    const timestamp = new Date(period.timestamp).toLocaleString();
                    report += `  ${timestamp} | ${period.window_seconds.toString().padStart(3)}s   | ${period.stability_score.toFixed(1).padStart(5)} | ${period.deviation_gh >= 0 ? '+' : ''}${period.deviation_gh.toFixed(1)} GH/s\n`;
                });
            }
            
            reportDisplay.innerHTML = report;
        }
        </script>
    '''

if __name__ == "__main__":
    print(add_variance_dashboard_html())
