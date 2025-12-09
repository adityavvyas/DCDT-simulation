import sys
import random
import math
import warnings
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer # Removed QThread

# --- ML/Data Imports ---
import pandas as pd
warnings.filterwarnings("ignore")

# --- Import from our project files ---
from ui.main_window import MainWindow
from data_pipeline import ScenarioCombinator, DataIngestor
from twin.digital_twin_engine import compute_results
from simulation.dynamics import StateRandomizer
from ml_engine import MLEngine            
# from ml_worker import MLCalibrationWorker # REMOVED
from unity_bridge import UnityBridge # NEW: Import Bridge

class WhatIfEngineController:
    
    # CALIBRATION_STEPS = 200 # REMOVED
    
    def __init__(self):
        print("Initializing components...")
        self.combinator = ScenarioCombinator()
        self.ingestor = DataIngestor()
        self.randomizer = StateRandomizer()
        self.current_ambient_temp = 25.0 
        
        # --- Unity Bridge Setup ---
        self.unity_bridge = UnityBridge() # Start the WebSocket server 
        
        # --- ML State Attributes ---
        self.simulation_step = 0
        forecast_features = ['average_pue', 'max_outlet_temp_c', 'total_power', 'total_daily_cost_usd']
        anomaly_features = ['average_pue', 'max_outlet_temp_c', 'total_power', 'total_compute_output']
        
        self.ml_engine = MLEngine(forecast_features, anomaly_features)
        
        # --- UI Setup ---
        self.view = MainWindow()
        self.view.simulation_requested.connect(self.run_simulation)
        self.view.suggest_tweaks_requested.connect(self.on_suggest_tweaks)
        self.view.auto_optimize_requested.connect(self.on_auto_optimize)
        
        # self.view.show_calibration_message() # REMOVED
        
        # --- Enable Optimizer buttons if models were loaded ---
        if self.ml_engine.optimizer_ready:
            self.view.suggest_button.setEnabled(True)
            self.view.optimize_button.setEnabled(True)
            self.view.profile_selector.setEnabled(True)
            self.view.suggestion_label.setText("AI co-pilot is ready. Select a profile.")
        else:
            self.view.suggestion_label.setText("Optimizer models not found. Run train_optimizer.py")
            self.view.suggest_button.setEnabled(False)
            self.view.optimize_button.setEnabled(False)
            self.view.profile_selector.setEnabled(False)
            
        # --- Simulation Timer ---
        self.simulation_timer = QTimer()
        self.simulation_timer.setInterval(1500)
        self.simulation_timer.timeout.connect(self.run_simulation)
        self.run_simulation() 
        self.simulation_timer.start()
        print("Continuous simulation started.")

    # --- MODIFIED: Optimizer Button Handlers ---
    
    def _get_selected_profile(self):
        """Reads the dropdown and returns the profile keyword."""
        raw_profile = self.view.profile_selector.currentText()
        if "Greedy" in raw_profile:
            return "greedy"
        elif "Sustainable" in raw_profile:
            return "sustainable"
        else:
            return "balanced"

    def on_suggest_tweaks(self):
        """Finds the best settings and displays them as a suggestion."""
        if not self.ml_engine.optimizer_ready:
            self.view.suggestion_label.setText("ML Optimizer is not ready. (models/ not found?)")
            return
            
        profile = self._get_selected_profile()
        suggestion = self.ml_engine.find_best_settings(self.current_ambient_temp, profile=profile)
        
        if suggestion:
            text = f"[ML SUGGESTION ({profile.upper()})]: Set Inlet to {suggestion['inlet']}°C " \
                   f"and Workload to {suggestion['workload']}% " \
                   f"for best results."
            self.view.suggestion_label.setText(text)
        else:
            self.view.suggestion_label.setText("Could not find an optimal solution.")

    def on_auto_optimize(self):
        """Finds the best settings, suggests them, AND applies them."""
        if not self.ml_engine.optimizer_ready:
            self.view.suggestion_label.setText("ML Optimizer is not ready. (models/ not found?)")
            return
            
        # 1. Get the suggestion
        profile = self._get_selected_profile()
        suggestion = self.ml_engine.find_best_settings(self.current_ambient_temp, profile=profile)
        
        if suggestion:
            text = f"[ML AUTO-PILOT ({profile.upper()})]: Set Inlet to {suggestion['inlet']}°C " \
                   f"and Workload to {suggestion['workload']}%."
            self.view.suggestion_label.setText(text)
            
            # 2. Apply the suggestion to the UI
            self.view.inlet_slider['slider'].setValue(suggestion['inlet'])
            self.view.inlet_slider['checkbox'].setChecked(True)
            
            self.view.workload_slider['slider'].setValue(suggestion['workload'])
            self.view.workload_slider['checkbox'].setChecked(True)
            
            # 3. Manually trigger a simulation run to show the new state
            self.run_simulation()
        else:
            self.view.suggestion_label.setText("Could not find an optimal solution.")

    # --- ML Training Thread ---
    # --- ALL CALIBRATION METHODS REMOVED ---
    # _start_ml_calibration REMOVED
    # on_calibration_complete REMOVED


    # --- Main Simulation Loop ---
    
    # --- REPLACED the entire run_simulation method ---
    def run_simulation(self):
        
        self.simulation_step += 1
        
        plan = self.combinator.generate_random_combination_plan()
        baseline_state = self.ingestor.get_state_from_plan(plan)
        baseline_payloads = [rack['payload'] for rack in baseline_state]
        varied_payloads = self.randomizer.apply_natural_variation(baseline_payloads)

        is_workload_override = self.view.workload_slider['checkbox'].isChecked()
        is_inlet_override = self.view.inlet_slider['checkbox'].isChecked()
        is_ambient_override = self.view.ambient_slider['checkbox'].isChecked()
        
        override_workload = self.view.workload_slider['slider'].value()
        override_inlet = self.view.inlet_slider['slider'].value()
        override_ambient = self.view.ambient_slider['slider'].value()
        
        if is_ambient_override:
            self.current_ambient_temp = override_ambient
        else:
            if varied_payloads: # Ensure list is not empty
                self.current_ambient_temp = sum(p['ambient_temp_c'] for p in varied_payloads) / len(varied_payloads)

        final_payloads = []
        for payload in varied_payloads:
            if is_workload_override: payload['server_workload_percent'] = max(0, min(100, override_workload + random.uniform(-2, 2)))
            if is_inlet_override: payload['inlet_temp_c'] = override_inlet
            if is_ambient_override: payload['ambient_temp_c'] = override_ambient
            final_payloads.append(payload)

        individual_results = [compute_results(p) for p in final_payloads]
        if not individual_results: return
        
        # --- NEW: Send Data to Unity ---
        unity_racks = []
        for i, res in enumerate(individual_results):
            temp = res['outlet_temp_c']
            status = "Normal"
            if temp > 37.0: status = "Critical"
            elif temp > 35.5: status = "Warning"
            
            rack_data = {
                "id": f"Rack_{i}",
                "index": i,
                "temperature": temp,
                "energy_usage": res['calculated_server_power_watts'],
                "status": status
            }
            unity_racks.append(rack_data)
        
        self.unity_bridge.send_update({"racks": unity_racks})
        # -------------------------------
        
        total_server_power_w = sum(r['calculated_server_power_watts'] for r in individual_results)
        total_cooling_power_w = sum(r['cooling_unit_power_watts'] for r in individual_results)
        total_facility_power_w = total_server_power_w + total_cooling_power_w
        avg_pue = total_facility_power_w / total_server_power_w if total_server_power_w > 0 else 0
        
        # These lines are now in the correct order
        max_outlet_temp = max(r['outlet_temp_c'] for r in individual_results)
        hottest_result = max(individual_results, key=lambda r: r['temp_deviation_c'])
        strategy = hottest_result.get('cooling_strategy', "STABLE")
        total_compute_output = sum(r['compute_output'] for r in individual_results)

        aggregated_results = {
            "total_server_power_kw": total_server_power_w / 1000,
            "total_cooling_power_kw": total_cooling_power_w / 1000,
            "average_pue": avg_pue,
            "max_outlet_temp_c": max_outlet_temp, # <-- THIS IS THE FIX
            "total_daily_cost_usd": (total_facility_power_w / 1000 * 0.12 * 24),
            "cooling_strategy": strategy,
            "individual_outlet_temps": [r['outlet_temp_c'] for r in individual_results],
            "individual_workloads": [p['server_workload_percent'] for p in final_payloads],
            "total_compute_output": total_compute_output
        }
        
        # --- NEW ML LOGIC ---
        # 1. Update models with the latest data
        self.ml_engine.update_and_refit(aggregated_results)
        
        # 2. Prepare data for inference
        current_features_df = pd.DataFrame([{
            'average_pue': aggregated_results['average_pue'],
            'max_outlet_temp_c': aggregated_results['max_outlet_temp_c'],
            'total_power': aggregated_results['total_server_power_kw'] + aggregated_results['total_cooling_power_kw'],
            'total_compute_output': aggregated_results['total_compute_output']
        }])[self.ml_engine.anomaly_features] 
            
        # 3. Run Anomaly Inference
        prediction = self.ml_engine.infer_anomaly(current_features_df)
            
        if prediction == -1: 
            if not (is_workload_override or is_inlet_override or is_ambient_override):
                self.view.alert_panel.add_alert(
                    "[ML INSIGHT] System operating outside normal parameters!", "warning"
                )

        # 4. Run Forecast Inference
        forecast_results = self.ml_engine.infer_forecasts()
        # --- END NEW ML LOGIC ---
        
        # 5. Update UI
        self.view.update_dashboard(aggregated_results, forecast_results)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    controller = WhatIfEngineController()
    controller.view.showMaximized() # Use showMaximized() for fullscreen
    sys.exit(app.exec_())

# --- MLCalibrationWorker class is REMOVED ---