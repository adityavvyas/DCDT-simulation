import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget,
                             QHBoxLayout, QLabel, QSlider, QFrame, QGridLayout, 
                             QCheckBox, QApplication, QScrollArea, QPushButton,
                             QSizePolicy, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPen, QPalette
from ui.dashboard_widgets import MetricGauge, TrendChart, AlertPanel, EnhancedHeatmap


class StatusIndicator(QLabel):
    """Custom label with status icon and color coding."""

    def __init__(self, text="", status="neutral"):
        super().__init__(text)
        self.status = status
        self.update_status(status, text)

    def update_status(self, status, text=None):
        self.status = status
        if text is not None:
            self.setText(text)

        font = QFont("Segoe UI", 11, QFont.Bold)
        self.setFont(font)

        if status == "good":
            self.setStyleSheet("font-family: 'Segoe UI'; color: #2ECC71; font-weight: bold; font-size: 11px;")
        elif status == "warning":
            self.setStyleSheet("font-family: 'Segoe UI'; color: #F39C12; font-weight: bold; font-size: 11px;")
        elif status == "critical":
            self.setStyleSheet("font-family: 'Segoe UI'; color: #E74C3C; font-weight: bold; font-size: 11px;")
        else:
            self.setStyleSheet("font-family: 'Segoe UI'; color: #7F8C8D; font-weight: normal; font-size: 11px;")


class MainWindow(QMainWindow):
    """Enhanced main UI window with tabs, charts, and advanced visualizations."""
    simulation_requested = pyqtSignal()
    suggest_tweaks_requested = pyqtSignal()
    auto_optimize_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Center Digital Twin - Operations Console")
        self.setStyleSheet("""
            QMainWindow { background-color: #0F0F1E; }
            
            QFrame { background-color: #1A1A2E; border-radius: 8px; border: 1px solid #2D2D4A; }
            QLabel { color: #ECF0F1; font-family: 'Segoe UI', Arial; }
            QSlider::groove:horizontal { background: #2D2D4A; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #4D96FF; width: 18px; margin: -5px 0; border-radius: 9px; }
            QCheckBox { color: #ECF0F1; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QCheckBox::indicator:checked { background-color: #4D96FF; border: 2px solid #4D96FF; border-radius: 3px; }
            QTabWidget::pane { border: 1px solid #2D2D4A; background: #0F0F1E; border-radius: 8px; }
            QTabBar::tab { background: #1A1A2E; color: #95A5A6; padding: 10px 20px; border: 1px solid #2D2D4A; 
                           border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
            QTabBar::tab:selected { background: #28284B; color: #4D96FF; font-weight: bold; }
            QTabBar::tab:hover { background: #252545; }
            
            QPushButton {
                background-color: #4D96FF;
                color: #FFFFFF;
                font-family: 'Segoe UI';
                font-weight: bold;
                font-size: 11px;
                border-radius: 6px;
                padding: 10px 16px;
                border: 1px solid #4D96FF;
            }
            QPushButton:hover { background-color: #60A5FF; }
            QPushButton:pressed { background-color: #3C80E0; }
            QPushButton#suggest {
                background-color: #1A1A2E;
                border: 2px solid #4D96FF;
                color: #4D96FF;
            }
            QPushButton#suggest:hover { background-color: #28284B; }
            QPushButton#suggest:pressed { background-color: #3C80E0; color: #FFFFFF; }
            
            QComboBox {
                background-color: #2D2D4A;
                color: #ECF0F1;
                padding: 10px 14px;
                border-radius: 5px;
                font-family: 'Segoe UI';
                font-size: 11px;
                border: 1px solid #3D3D5C;
            }
            QComboBox::drop-down { 
                border: none; 
                width: 20px; 
            }
            QComboBox QAbstractItemView {
                background-color: #1A1A2E;
                color: #ECF0F1;
                selection-background-color: #4D96FF;
                selection-color: #FFFFFF;
                border: 1px solid #3D3D5C;
                padding: 5px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                background-color: #1A1A2E;
                color: #ECF0F1;
                padding: 8px 12px;
                border: none;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #4D96FF;
                color: #FFFFFF;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #28284B;
            }
            
            QScrollBar:vertical {
                background: #1A1A2E;
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #3D3D5C;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4D96FF;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
                subcontrol-origin: margin;
            }
        """)

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: #0F0F1E;") # Force dark background
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Create tab widget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Create different views
        self._create_overview_tab()
        self._create_analytics_tab()
        self._create_thermal_tab()

    def _create_overview_tab(self):
        """Main overview dashboard with key metrics and controls."""
        
        overview_tab = QWidget()
        tab_layout = QVBoxLayout(overview_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        tab_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        
        control_panel = self._create_control_panel()
        top_row.addWidget(control_panel, 1)
        
        gauges_panel = QFrame()
        gauges_layout = QHBoxLayout(gauges_panel)
        gauges_layout.setSpacing(20)
        gauges_layout.setContentsMargins(10, 10, 10, 10)
        
        self.pue_gauge = MetricGauge("PUE", 1.0, 3.0, "", 1.6, 1.9, reverse_colors=True)
        self.temp_gauge = MetricGauge("Max Temp", 20, 50, "°C", 35.5, 37.0, reverse_colors=True)
        self.power_gauge = MetricGauge("Total Power", 0, 2000, "kW", 1200, 1600, reverse_colors=True)
        
        gauges_layout.addWidget(self.pue_gauge)
        gauges_layout.addWidget(self.temp_gauge)
        gauges_layout.addWidget(self.power_gauge)
        
        top_row.addWidget(gauges_panel, 1)
        layout.addLayout(top_row)
        
        middle_row = QHBoxLayout()
        middle_row.setSpacing(20)
        
        summary_panel = self._create_summary_panel()
        middle_row.addWidget(summary_panel, 1)
        
        self.alert_panel = AlertPanel()
        middle_row.addWidget(self.alert_panel, 1)
        
        layout.addLayout(middle_row)
        
        heatmap_frame = QFrame()
        heatmap_layout = QVBoxLayout(heatmap_frame)
        heatmap_layout.setContentsMargins(20, 20, 20, 20)
        heatmap_title = QLabel("Rack Thermal Overview")
        heatmap_title.setStyleSheet("font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; color: #4D96FF; margin-bottom: 10px;")
        heatmap_layout.addWidget(heatmap_title)
        
        self.overview_heatmap = EnhancedHeatmap(rows=20, cols=35)
        heatmap_layout.addWidget(self.overview_heatmap)
        
        layout.addWidget(heatmap_frame)
        
        self.tabs.addTab(overview_tab, "📊 Overview")
    
    def _create_control_panel(self):
        """Create the control panel with sliders."""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("What-If Scenario Controls")
        title.setStyleSheet("font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; margin-bottom: 8px; color: #4D96FF;")
        layout.addWidget(title)

        desc = QLabel("☑ Enable overrides to simulate conditions")
        desc.setStyleSheet("font-family: 'Segoe UI'; font-size: 10px; color: #95A5A6; margin-bottom: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.workload_slider = self._create_slider_control("Avg Server Workload (%)", 0, 100, 50)
        layout.addLayout(self.workload_slider['layout'])

        self.inlet_slider = self._create_slider_control("Global Inlet Temp (°C)", 15, 30, 22)
        layout.addLayout(self.inlet_slider['layout'])

        self.ambient_slider = self._create_slider_control("Global Ambient Temp (°C)", 10, 45, 25)
        layout.addLayout(self.ambient_slider['layout'])

        layout.addStretch(1) # Add space
        
        ai_title = QLabel("AI Optimization Engine")
        ai_title.setStyleSheet("font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; margin-bottom: 8px; margin-top: 10px; color: #4D96FF;")
        layout.addWidget(ai_title)

        profile_label = QLabel("Select Optimization Profile:")
        profile_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 11px; color: #95A5A6; margin-bottom: 5px;")
        layout.addWidget(profile_label)
        
        self.profile_selector = QComboBox()
        self.profile_selector.addItems(["Balanced (Best Value)", "Greedy (Max Compute)", "Sustainable (Min Cost)"])
        
        # Force dark background on dropdown list view
        view = self.profile_selector.view()
        palette = view.palette()
        palette.setColor(QPalette.Base, QColor("#1A1A2E"))
        palette.setColor(QPalette.Text, QColor("#ECF0F1"))
        palette.setColor(QPalette.Highlight, QColor("#4D96FF"))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        palette.setColor(QPalette.Window, QColor("#1A1A2E"))
        view.setPalette(palette)
        
        layout.addWidget(self.profile_selector)

        self.suggestion_label = QLabel("Run 'Suggest Tweaks' for AI co-pilot.")
        self.suggestion_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 11px; color: #BDC3C7; padding: 12px; border: 1px dashed #3D3D5C; border-radius: 5px; margin-top: 10px;")
        self.suggestion_label.setWordWrap(True)
        self.suggestion_label.setMinimumHeight(55)
        layout.addWidget(self.suggestion_label)
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)
        
        self.suggest_button = QPushButton("💡 Suggest Tweaks")
        self.suggest_button.setObjectName("suggest") # For styling
        self.suggest_button.clicked.connect(self.suggest_tweaks_requested)
        
        self.optimize_button = QPushButton("✨ Auto-Optimize")
        self.optimize_button.clicked.connect(self.auto_optimize_requested)
        
        button_layout.addWidget(self.suggest_button)
        button_layout.addWidget(self.optimize_button)
        
        layout.addLayout(button_layout)
        layout.addStretch(1)
        
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        return panel

    def _handle_slider_interaction(self, checkbox):
        if checkbox.isChecked():
            self.simulation_requested.emit()

    def _create_slider_control(self, name, min_val, max_val, initial_val):
        """Helper to create a checkbox, label, and slider group."""
        checkbox = QCheckBox()
        checkbox.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }")

        label = QLabel(f"{name}: {initial_val}")
        label.setStyleSheet("font-family: 'Segoe UI'; color: #ECF0F1; font-size: 11px;")

        value_display = QLabel(f"{initial_val}")
        value_display.setStyleSheet("font-family: 'Segoe UI'; color: #4D96FF; font-size: 13px; font-weight: bold; min-width: 45px;")

        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(initial_val)

        def update_display(value):
            label.setText(f"{name}: {value}")
            value_display.setText(f"{value}")

        slider.valueChanged.connect(update_display)
        checkbox.stateChanged.connect(self.simulation_requested.emit)
        slider.valueChanged.connect(lambda: self._handle_slider_interaction(checkbox))

        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.addWidget(checkbox)
        layout.addWidget(label, 0)
        layout.addWidget(value_display, 0)
        layout.addWidget(slider, 2)
        layout.setContentsMargins(0, 6, 0, 6)

        return {"layout": layout, "slider": slider, "label": label, "checkbox": checkbox}

    def _create_summary_panel(self):
        """Create summary metrics panel."""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Current Metrics")
        title.setStyleSheet("font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; margin-bottom: 10px; color: #4D96FF;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(15)
        grid.setContentsMargins(0, 0, 0, 0)

        self.result_labels = {}
        self.status_indicators = {}

        metrics = [
            ("Total Server Power (kW)", "power"),
            ("Total Cooling Power (kW)", "power"),
            ("Average PUE", "pue"),
            ("MAX Outlet Temp (°C)", "temp"),
            ("Total Compute Output", "compute"),
            ("Projected Daily Cost (USD)", "cost"),
            ("Cooling Strategy", "strategy")
        ]

        for i, (name, metric_type) in enumerate(metrics):
            name_label = QLabel(name)
            name_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 11px; color: #95A5A6; font-weight: 600;")

            value_label = QLabel("N/A")
            value_label.setStyleSheet("font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; color: #ECF0F1;")

            status_label = StatusIndicator("", "neutral")

            grid.addWidget(name_label, i, 0, Qt.AlignLeft)
            grid.addWidget(value_label, i, 1, Qt.AlignLeft)
            grid.addWidget(status_label, i, 2, Qt.AlignLeft)

            self.result_labels[name] = value_label
            self.status_indicators[name] = (status_label, metric_type)

        layout.addLayout(grid)
        layout.addStretch()
        return panel

    def _create_analytics_tab(self):
        """Analytics tab with trend charts."""
        
        analytics_tab = QWidget()
        tab_layout = QVBoxLayout(analytics_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        tab_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("Performance Analytics & Trends")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4D96FF; margin-bottom: 8px;")
        layout.addWidget(title)

        top_charts = QHBoxLayout()
        
        # --- UPDATED: Pass static range and goal text to charts ---
        self.pue_chart = TrendChart("PUE Trend", max_points=60, y_label="PUE", color="#4D96FF", 
                                    forecast_steps=30, goal_text="Lower is Better", y_min=1.0, y_max=2.5)
        
        self.temp_chart = TrendChart("Temperature Trend", max_points=60, y_label="°C", color="#E74C3C", 
                                     forecast_steps=30, goal_text="Lower is Better", y_min=30, y_max=50)
        
        top_charts.addWidget(self.pue_chart)
        top_charts.addWidget(self.temp_chart)
        layout.addLayout(top_charts)

        bottom_charts = QHBoxLayout()
        self.power_chart = TrendChart("Total Power Trend", max_points=60, y_label="kW", color="#2ECC71", 
                                      forecast_steps=30, goal_text="Lower is Better", y_min=1000, y_max=2000)
        
        self.cost_chart = TrendChart("Cost Trend", max_points=60, y_label="USD/day", color="#F1C40F", 
                                     forecast_steps=30, goal_text="Lower is Better", y_min=3000, y_max=6000)
        # --- End of Update ---
        
        bottom_charts.addWidget(self.power_chart)
        bottom_charts.addWidget(self.cost_chart)
        layout.addLayout(bottom_charts)

        insights_frame = QFrame()
        insights_layout = QVBoxLayout(insights_frame)
        insights_title = QLabel("Efficiency Insights")
        insights_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #4D96FF;")
        insights_layout.addWidget(insights_title)
        
        self.insights_label = QLabel("Analyzing datacenter performance...")
        # --- UPDATED: Increased font size ---
        self.insights_label.setStyleSheet("font-size: 11px; color: #BDC3C7; padding: 8px;")
        self.insights_label.setWordWrap(True)
        insights_layout.addWidget(self.insights_label)
        
        layout.addWidget(insights_frame)
        
        self.tabs.addTab(analytics_tab, "📈 Analytics")
    
    def _create_thermal_tab(self):
        """Thermal management tab with detailed heatmap."""
        
        thermal_tab = QWidget()
        tab_layout = QVBoxLayout(thermal_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        tab_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("Thermal Management - Live Rack Heatmap (700 Racks)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4D96FF; margin-bottom: 8px;")
        layout.addWidget(title)

        legend_layout = QHBoxLayout()
        legend_label = QLabel("Temperature Status:")
        legend_label.setStyleSheet("color: #BDC3C7; font-size: 10px; font-weight: bold;")
        legend_layout.addWidget(legend_label)
        
        for color, label in [("#2ECC71", "Good < 35.5°C"), ("#F1C40F", "Warning 35.5-37°C"),
                             ("#E74C3C", "Critical > 37°C")]:
            color_box = QLabel()
            color_box.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
            color_box.setFixedSize(15, 15)
            legend_text = QLabel(label)
            legend_text.setStyleSheet("color: #BDC3C7; font-size: 9px;")
            legend_layout.addWidget(color_box)
            legend_layout.addWidget(legend_text)
            legend_layout.addSpacing(15)

        legend_layout.addStretch()
        layout.addLayout(legend_layout)

        self.heatmap = EnhancedHeatmap(rows=20, cols=35)
        layout.addWidget(self.heatmap)

        stats_frame = QFrame()
        stats_layout = QHBoxLayout(stats_frame)
        self.thermal_stats_labels = {}
        for stat_name in ["Hottest Rack", "Coldest Rack", "Avg Temp", "Racks in Warning", "Racks Critical"]:
            stat_container = QVBoxLayout()
            name_label = QLabel(stat_name)
            name_label.setStyleSheet("font-size: 9px; color: #95A5A6;")
            value_label = QLabel("N/A")
            value_label.setStyleSheet("font-size: 11px; color: #FFFFFF; font-weight: bold;")
            stat_container.addWidget(name_label)
            stat_container.addWidget(value_label)
            stats_layout.addLayout(stat_container)
            self.thermal_stats_labels[stat_name] = value_label
        
        layout.addWidget(stats_frame)
        
        self.tabs.addTab(thermal_tab, "🌡️ Thermal")

    def show_calibration_message(self):
        """Displays the 'Calibrating' message on startup."""
        self.alert_panel.add_alert("ML Engine: CALIBRATING... Please wait.", "info")
        self.insights_label.setText("ML Engine is calibrating...\nThis may take a moment as it learns 'normal' operations.")

    def hide_calibration_message(self):
        """Hides the 'Calibrating' message and shows 'Online'."""
        self.alert_panel.add_alert("ML Engine: CALIBRATED. System online.", "good")

    def update_dashboard(self, results, forecasts={}):
        """
        Update all dashboard elements with new simulation results.
        """
        server_power = results.get('total_server_power_kw', 0)
        cooling_power = results.get('total_cooling_power_kw', 0)
        total_power = server_power + cooling_power
        pue = results.get('average_pue', 0)
        max_temp = results.get('max_outlet_temp_c', 0)
        daily_cost = results.get('total_daily_cost_usd', 0)
        compute_output = results.get('total_compute_output', 0)
        strategy = results.get('cooling_strategy', 'N/A')
        temps = results.get('individual_outlet_temps', [])
        workloads = results.get('individual_workloads', [])

        self.result_labels["Total Server Power (kW)"].setText(f"{server_power:.1f} kW")
        self.result_labels["Total Cooling Power (kW)"].setText(f"{cooling_power:.1f} kW")
        self.result_labels["Average PUE"].setText(f"{pue:.2f}")
        self.result_labels["MAX Outlet Temp (°C)"].setText(f"{max_temp:.1f}°C")
        self.result_labels["Total Compute Output"].setText(f"{compute_output:,.0f}")
        self.result_labels["Projected Daily Cost (USD)"].setText(f"${daily_cost:,.0f}")
        
        clean_strategy = strategy.replace("[bold red]", "").replace("[bold red]", "")
        clean_strategy = clean_strategy.replace("[bold yellow]", "").replace("[bold yellow]", "")
        clean_strategy = clean_strategy.replace("[bold green]", "").replace("[bold green]", "")
        self.result_labels["Cooling Strategy"].setText(clean_strategy)

        self.pue_gauge.set_value(pue)
        self.temp_gauge.set_value(max_temp)
        self.power_gauge.set_value(total_power)

        pue_status = "good" if pue < 1.6 else "warning" if pue < 1.9 else "critical"
        pue_text = "✓ Excellent" if pue_status == "good" else "⚠ Fair" if pue_status == "warning" else "✗ Poor"
        self.status_indicators["Average PUE"][0].update_status(pue_status, pue_text)

        temp_status = "good" if max_temp < 35.5 else "warning" if max_temp < 37 else "critical"
        temp_text = "✓ Normal" if temp_status == "good" else "⚠ High" if temp_status == "warning" else "✗ Critical"
        self.status_indicators["MAX Outlet Temp (°C)"][0].update_status(temp_status, temp_text)

        power_status = "good" if total_power < 1200 else "warning" if total_power < 1600 else "critical"
        power_text = "✓ Normal" if power_status == "good" else "⚠ High" if power_status == "warning" else "✗ Very High"
        self.status_indicators["Total Server Power (kW)"][0].update_status(power_status, power_text)
        self.status_indicators["Total Cooling Power (kW)"][0].update_status(power_status, power_text)
        
        self.status_indicators["Total Compute Output"][0].update_status("neutral", "")
        self.status_indicators["Projected Daily Cost (USD)"][0].update_status("neutral", "")
        self.status_indicators["Cooling Strategy"][0].update_status("neutral", "")

        self.heatmap.update_data(temps, workloads)
        self.overview_heatmap.update_data(temps, workloads)

        self.pue_chart.add_data_point(pue)
        self.temp_chart.add_data_point(max_temp)
        self.power_chart.add_data_point(total_power)
        self.cost_chart.add_data_point(daily_cost)

        if forecasts:
            self.pue_chart.update_forecast_data(forecasts.get('pue', []))
            self.temp_chart.update_forecast_data(forecasts.get('temp', []))
            self.power_chart.update_forecast_data(forecasts.get('power', []))
            self.cost_chart.update_forecast_data(forecasts.get('cost', []))

        if temps:
            avg_temp = sum(temps) / len(temps) if temps else 0
            hottest_idx = temps.index(max(temps)) if temps else 0
            coldest_idx = temps.index(min(temps)) if temps else 0
            warning_count = sum(1 for t in temps if 35.5 <= t < 37.0)
            critical_count = sum(1 for t in temps if t >= 37.0)

            self.thermal_stats_labels["Hottest Rack"].setText(f"#{hottest_idx + 1} ({max(temps) if temps else 'N/A':.1f}°C)")
            self.thermal_stats_labels["Coldest Rack"].setText(f"#{coldest_idx + 1} ({min(temps) if temps else 'N/A':.1f}°C)")
            self.thermal_stats_labels["Avg Temp"].setText(f"{avg_temp:.1f}°C")
            
            warning_label = self.thermal_stats_labels["Racks in Warning"]
            warning_label.setText(f"{warning_count}")
            warning_label.setStyleSheet(f"font-size: 11px; color: {'#F39C12' if warning_count > 50 else '#ECF0F1'}; font-weight: bold;")
            
            critical_label = self.thermal_stats_labels["Racks Critical"]
            critical_label.setText(f"{critical_count}")
            if critical_count > 20:
                critical_label.setStyleSheet("font-size: 11px; color: #E74C3C; font-weight: bold;")
            elif critical_count > 0:
                critical_label.setStyleSheet("font-size: 11px; color: #F39C12; font-weight: bold;")
            else:
                critical_label.setStyleSheet("font-size: 11px; color: #2ECC71; font-weight: bold;")

        if pue > 2.0: self.alert_panel.add_alert(f"PUE critical at {pue:.2f} - Cooling inefficient", "critical")
        elif pue > 1.9: self.alert_panel.add_alert(f"PUE elevated at {pue:.2f} - Review cooling", "warning")
        if max_temp > 40.0: self.alert_panel.add_alert(f"Extreme temperature: {max_temp:.1f}°C - Immediate action required", "critical")
        elif max_temp > 37.0: self.alert_panel.add_alert(f"Critical temperature: {max_temp:.1f}°C", "critical")
        elif max_temp > 35.5: self.alert_panel.add_alert(f"Temperature elevated: {max_temp:.1f}°C", "warning")
        if critical_count > 50: self.alert_panel.add_alert(f"{critical_count} racks critical - System overload", "critical")
        elif critical_count > 20: self.alert_panel.add_alert(f"{critical_count} racks in critical state", "warning")
        if total_power > 1800: self.alert_panel.add_alert(f"Power consumption very high: {total_power:.0f} kW", "critical")
        elif total_power > 1600: self.alert_panel.add_alert(f"Power consumption elevated: {total_power:.0f} kW", "warning")

        if hasattr(self, 'insights_label'):
             # Logic to update insights label
            if "ML Engine is calibrating" in self.insights_label.text() and len(forecasts) > 0:
                 self.insights_label.setText("ML Engine is online. Analyzing performance...")
            
            if len(forecasts) > 0: # Only show insights if ML is running
                efficiency_score = 100 - ((pue - 1.0) * 50)
                thermal_score = 100 - max(0, (max_temp - 30) * 5)
                overall_score = (efficiency_score + thermal_score) / 2

                insights = f"Overall Efficiency Score: {overall_score:.0f}/100\n\n"
                insights += f"• PUE Efficiency: {efficiency_score:.0f}/100 "
                insights += f"({'Excellent' if pue < 1.6 else 'Good' if pue < 1.8 else 'Needs Improvement'})\n"
                insights += f"• Thermal Management: {thermal_score:.0f}/100 "
                insights += f"({'Optimal' if max_temp < 35 else 'Acceptable' if max_temp < 37 else 'Critical'})\n"
                insights += f"• Estimated Annual Cost: ${daily_cost * 365:,.0f}\n\n"
                
                if pue > 1.8: insights += "💡 Recommendation: Reduce cooling overhead or optimize airflow.\n"
                if max_temp > 36: insights += "💡 Recommendation: Increase cooling capacity or reduce workload on hot racks.\n"
                if overall_score > 80: insights += "✓ Datacenter is operating efficiently!"
                
                self.insights_label.setText(insights)