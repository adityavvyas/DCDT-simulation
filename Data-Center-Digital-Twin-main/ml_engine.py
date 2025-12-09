import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.arima.model import ARIMA
import warnings
import joblib
import os
from collections import deque # Import deque

# Suppress harmless warnings from statsmodels
warnings.filterwarnings("ignore")

class MLEngine:
    """
    Encapsulates all Machine Learning logic for the Digital Twin.
    """
    
    # --- MODIFIED: __init__ ---
    def __init__(self, forecast_features, anomaly_features, forecast_steps=30):
        
        # 1. Set ml_ready to True immediately
        self.ml_ready = True 
        self.history_buffer = deque(maxlen=200) # Use a deque for history
        
        # 2. Initialize models right away
        self.anomaly_detector = IsolationForest(contamination=0.05, random_state=42)
        self.forecasters = {}
        
        self.forecast_features = forecast_features
        self.anomaly_features = anomaly_features
        self.forecast_steps = forecast_steps
        
        # --- Optimizer (no change) ---
        self.optimizer_ready = False
        self.cost_model = None
        self.compute_model = None
        self.optimizer_features = ['ambient_temp_c', 'inlet_temp_c', 'server_workload_percent']
        
        self._load_optimizer_models()

    def _load_optimizer_models(self):
        """Loads the pre-trained optimizer models from disk."""
        cost_path = "models/optimizer_cost.joblib"
        compute_path = "models/optimizer_compute.joblib"
        
        if os.path.exists(cost_path) and os.path.exists(compute_path):
            try:
                self.cost_model = joblib.load(cost_path)
                self.compute_model = joblib.load(compute_path)
                self.optimizer_ready = True
                print("ML OPTIMIZER: Models loaded successfully.")
            except Exception as e:
                print(f"ML OPTIMIZER: Error loading models: {e}")
        else:
            print("ML OPTIMIZER: Warning! Optimizer models not found. Run train_optimizer.py")
            
    # --- MODIFIED: The "Finder" Function ---
    def find_best_settings(self, current_ambient_temp, profile="balanced", num_samples=1000):
        """
        Uses the loaded models to find the optimal settings for the given ambient temp
        based on the selected optimization profile.
        """
        if not self.optimizer_ready:
            return None

        print(f"ML OPTIMIZER: Searching for '{profile}' settings at {current_ambient_temp:.1f}°C ambient...")
        
        # 1. Create a "search space" DataFrame
        search_data = {
            'ambient_temp_c': np.full(num_samples, current_ambient_temp),
            'inlet_temp_c': np.random.uniform(15, 30, num_samples),
            'server_workload_percent': np.random.uniform(20, 100, num_samples) # Assume we want at least 20% work
        }
        search_df = pd.DataFrame(search_data)[self.optimizer_features]

        # 2. Predict cost and compute for all samples
        pred_cost = self.cost_model.predict(search_df)
        pred_compute = self.compute_model.predict(search_df)

        # 3. --- NEW: Find the best "reward" based on the profile ---
        if profile == "greedy":
            # Maximize compute, ignore cost
            reward = pred_compute
        elif profile == "sustainable":
            # Maximize 1 / cost (i.e., minimize cost)
            reward = 1 / (pred_cost + 1) # +1 to avoid divide-by-zero
        else: # "balanced"
            # Maximize compute-per-dollar (default)
            reward = pred_compute / (pred_cost + 1)
        
        best_index = np.argmax(reward)
        
        best_settings = search_df.iloc[best_index]
        
        return {
            'inlet': int(best_settings['inlet_temp_c']),
            'workload': int(best_settings['server_workload_percent']),
            'reward_score': reward[best_index]
        }

    # --- 'add_to_buffer' and 'calibrate' are REMOVED ---
    
    # --- ADDED this NEW 'update_and_refit' method ---
    def update_and_refit(self, data_dict):
        """
        Adds a new data point and refits all ML models.
        This is called on every simulation step.
        """
        self.history_buffer.append(data_dict)
        
        # We need *some* data to train, > 20 steps is a safe minimum to avoid errors
        if len(self.history_buffer) < 20:
            print(f"ML: Collecting initial data... {len(self.history_buffer)}/20")
            
            # --- Enable optimizer buttons once we have *some* data ---
            if len(self.history_buffer) == 19 and self.optimizer_ready:
                 print("ML: Optimizer is now online.")
            return 
        
        # --- Update insights message once training starts ---
        if len(self.history_buffer) == 20:
            print("ML: Initial data collected. Live training starting.")

        df = pd.DataFrame(self.history_buffer)
        df['total_power'] = df['total_server_power_kw'] + df['total_cooling_power_kw']

        # 1. Re-Train Anomaly Detection Model
        try:
            anomaly_data = df[self.anomaly_features]
            self.anomaly_detector.fit(anomaly_data)
        except Exception as e:
            print(f"ML Error (Anomaly): {e}")

        # 2. Re-Train Forecasting Models
        try:
            for feature in self.forecast_features:
                # (Re-training ARIMA every step is slow, but works for this demo)
                model = ARIMA(df[feature], order=(1, 0, 0)) 
                model_fit = model.fit()
                self.forecasters[feature] = model_fit
        except Exception as e:
            # This can fail if data is all the same (e.g., in override)
            # print(f"ML Error (Forecast): {e}")
            pass # Suppress repeat warnings

    def infer_anomaly(self, current_data_df):
        """
        Runs anomaly detection on the current data point.
        """
        if not self.ml_ready or self.anomaly_detector is None or len(self.history_buffer) < 20:
            return 0 
            
        try:
            prediction = self.anomaly_detector.predict(current_data_df)
            return prediction[0]
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return 0

    def infer_forecasts(self):
        """
        Generates a forecast for all relevant features.
        """
        if not self.ml_ready or not self.forecasters or len(self.history_buffer) < 20:
            return {}
            
        forecast_results = {}
        try:
            for feature, model in self.forecasters.items():
                history_len = model.nobs
                start = history_len
                end = history_len + self.forecast_steps - 1
                
                forecast = list(model.predict(start, end))
                clean_key = feature.replace('total_power', 'power') \
                                   .replace('average_pue', 'pue') \
                                   .replace('max_outlet_temp_c', 'temp') \
                                   .replace('total_daily_cost_usd', 'cost')
                forecast_results[clean_key] = forecast
        
        except Exception as e:
            # print(f"Forecasting error: {e}")
            return {}
            
        return forecast_results