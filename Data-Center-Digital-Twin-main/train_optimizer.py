import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
import sys
import os

# --- IMPORTANT: Add project root to path ---
# This ensures we can import from 'twin'
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now we can import our core physics
from twin.digital_twin_engine import compute_results

print("Starting optimizer training script...")

# 1. Generate a large synthetic dataset
NUM_SAMPLES = 50000
print(f"Generating {NUM_SAMPLES} data samples...")

data = {
    'ambient_temp_c': np.random.uniform(10, 45, NUM_SAMPLES),
    'inlet_temp_c': np.random.uniform(15, 30, NUM_SAMPLES),
    'server_workload_percent': np.random.uniform(0, 100, NUM_SAMPLES)
}
df = pd.DataFrame(data)

# 2. Run the Digital Twin physics for each sample
print("Running physics simulation for all samples...")
results = []
for _, row in df.iterrows():
    # We pass the row as the 'payload' for the compute function
    sim_result = compute_results(row.to_dict())
    
    cost_per_day = (sim_result['calculated_server_power_watts'] + sim_result['cooling_unit_power_watts']) / 1000 * 0.12 * 24
    
    results.append({
        'cost_per_day': cost_per_day,
        'compute_output': sim_result['compute_output']
    })

results_df = pd.DataFrame(results)
df = pd.concat([df, results_df], axis=1)

# 3. Define our features (X) and targets (y)
features = ['ambient_temp_c', 'inlet_temp_c', 'server_workload_percent']
X = df[features]
y_cost = df['cost_per_day']
y_compute = df['compute_output']

print("Data generation complete. Training models...")

# 4. Train the Cost Prediction Model
cost_model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1, max_depth=10)
cost_model.fit(X, y_cost)
print("Cost model trained.")

# 5. Train the Compute Prediction Model
compute_model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1, max_depth=10)
compute_model.fit(X, y_compute)
print("Compute model trained.")

# 6. Save models to disk
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)

cost_model_path = os.path.join(model_dir, "optimizer_cost.joblib")
compute_model_path = os.path.join(model_dir, "optimizer_compute.joblib")

joblib.dump(cost_model, cost_model_path)
joblib.dump(compute_model, compute_model_path)

print(f"Models saved successfully to '{model_dir}' directory.")
print("Optimizer training complete.")