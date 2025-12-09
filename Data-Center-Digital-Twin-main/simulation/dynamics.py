import random
import math
from datetime import datetime

class StateRandomizer:
    """
    Applies a layer of dynamic, "natural" variation on top of a baseline
    data state to make the simulation feel alive and unpredictable.
    """
    def __init__(self):
        self.simulation_hour = datetime.now().hour
        print(f"StateRandomizer initialized. Starting at hour: {self.simulation_hour}.")

    def _get_diurnal_multiplier(self, hour, peak_multiplier, trough_multiplier):
        """Creates a simple day/night cycle multiplier (e.g., 1.2 for day, 0.8 for night)."""
        sine_wave = math.sin(math.pi * (hour - 8) / 12)
        multiplier_range = peak_multiplier - trough_multiplier
        return trough_multiplier + (1 + sine_wave) / 2 * multiplier_range

    def apply_natural_variation(self, baseline_payloads):
        """
        Takes a list of baseline payloads and returns a new list with
        dynamic variations applied.
        """
        # Get the global multipliers for the current simulated hour
        workload_multiplier = self._get_diurnal_multiplier(self.simulation_hour, 1.2, 0.7) # 20% higher in day, 30% lower at night
        ambient_multiplier = self._get_diurnal_multiplier(self.simulation_hour, 1.1, 0.9)  # 10% temp swing

        if 12 <= self.simulation_hour <= 13: # Lunchtime dip
            workload_multiplier *= 0.8 

        varied_payloads = []
        for payload in baseline_payloads:
            new_payload = payload.copy()

            # Apply multiplier and random noise to the baseline workload
            base_workload = new_payload['server_workload_percent']
            varied_workload = base_workload * workload_multiplier + random.uniform(-5, 5)
            
            # Add occasional random spikes for realism
            if random.random() < 0.02:
                varied_workload += random.uniform(15, 30)

            # Apply multiplier and noise to ambient temperature
            base_ambient = new_payload['ambient_temp_c']
            varied_ambient = base_ambient * ambient_multiplier + random.uniform(-1, 1)

            new_payload['server_workload_percent'] = max(5, min(100, varied_workload))
            new_payload['ambient_temp_c'] = varied_ambient
            
            varied_payloads.append(new_payload)

        # Advance the simulation time for the next cycle
        self.simulation_hour = (self.simulation_hour + 1) % 24
        
        return varied_payloads

