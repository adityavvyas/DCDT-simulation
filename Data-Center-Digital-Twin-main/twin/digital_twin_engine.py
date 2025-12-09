import random
from typing import Dict, Any

class DataCenterTwin:
    """The core physics engine, now with a realistic cooling feedback loop."""
    def __init__(self):
        self.SERVER_MAX_POWER_WATTS = 1440
        self.SERVER_IDLE_POWER_WATTS = 210
        self.HEAT_DISSIPATION_FACTOR = 0.0117
        self.COOLING_BASE_POWER_WATTS = 400
        self.COOLING_EFFICIENCY_FACTOR = 0.42
        self.AMBIENT_TEMP_IMPACT_FACTOR = 15
        self.IDEAL_AMBIENT_TEMP_C = 20.0
        self.TARGET_OUTLET_TEMP_C = 35.0
        self.COST_PER_KWH_USD = 0.12
        self.IDEAL_INLET_TEMP_C = 25.0
        self.INLET_TEMP_IMPACT_FACTOR = 25
        
        # NEW: A factor to model how much the inlet temp rises if cooling is insufficient.
        # This simulates the air not getting cold enough if the system is overwhelmed.
        self.COOLING_DEFICIT_TEMP_FACTOR = 0.005 # e.g., a 100W deficit raises inlet temp by 0.5°C

    def _get_cooling_strategy(self, temp_deviation, pue):
        if temp_deviation > 2.0: return "[bold red]CRITICAL: Boost All Cooling[/bold red]"
        elif temp_deviation > 0.5: return "[bold yellow]WARNING: Increase Cooling[/bold yellow]"
        elif pue > 1.8: return "[bold yellow]EFFICIENCY ALERT: Optimize Cooling[/bold yellow]"
        else: return "[bold green]STABLE: Monitor[/bold green]"

    def compute_results(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # --- The 'inlet_temp_c' from the payload is now treated as the TARGET inlet temp ---
        target_inlet_temp_c = float(payload.get("inlet_temp_c", 22.0) or 22.0)
        server_workload_percent = float(payload.get("server_workload_percent", 0.0) or 0.0)
        ambient_temp_c = float(payload.get("ambient_temp_c", 25.0) or 25.0)

        # 1. Server Power and Heat (Unchanged)
        server_power_watts = self.SERVER_IDLE_POWER_WATTS + \
                             (server_workload_percent / 100) * (self.SERVER_MAX_POWER_WATTS - self.SERVER_IDLE_POWER_WATTS)
        heat_generated = server_power_watts

        # 2. NEW: Calculate the ACTUAL inlet temperature with a feedback loop
        # First, calculate the total power the cooling system *needs* to consume
        required_cooling_power = (
            self.COOLING_BASE_POWER_WATTS +
            (heat_generated * self.COOLING_EFFICIENCY_FACTOR) +
            max(0, (ambient_temp_c - self.IDEAL_AMBIENT_TEMP_C)) * self.AMBIENT_TEMP_IMPACT_FACTOR +
            max(0, (self.IDEAL_INLET_TEMP_C - target_inlet_temp_c)) * self.INLET_TEMP_IMPACT_FACTOR
        )

        # For this model, we'll assume the cooling power is what's required, as we don't have a max cap.
        # The "strain" on the system is represented by the total power it's forced to draw.
        # A more advanced model could cap this, creating a "deficit."
        # For our purposes, we can model the feedback by making the actual inlet temp dependent on the ambient.
        # This creates the link you were looking for.
        ambient_strain_effect = max(0, (ambient_temp_c - self.IDEAL_AMBIENT_TEMP_C)) * 0.1 # Strain from hot weather raises inlet temp
        workload_strain_effect = (server_power_watts / self.SERVER_MAX_POWER_WATTS) * 0.5 # Higher workload slightly raises inlet temp
        
        actual_inlet_temp_c = target_inlet_temp_c + ambient_strain_effect + workload_strain_effect

        # 3. Calculate Outlet Temperature using the new, DYNAMIC actual inlet temp
        outlet_temp_c = actual_inlet_temp_c + (server_power_watts * self.HEAT_DISSIPATION_FACTOR)

        # 4. Final cooling power and metrics
        # The cooling power is the required power calculated earlier
        cooling_unit_power_watts = required_cooling_power
        total_power_watts = server_power_watts + cooling_unit_power_watts
        pue = total_power_watts / server_power_watts if server_power_watts > 0 else 0
        temp_deviation_c = outlet_temp_c - self.TARGET_OUTLET_TEMP_C
        strategy = self._get_cooling_strategy(temp_deviation_c, pue)
        
        # --- This part is unchanged ---
        base_compute_output = (server_workload_percent / 100) * 10000
        throttling_penalty = 0.0
        if outlet_temp_c > 38.0:
            throttling_penalty = min(1.0, (outlet_temp_c - 38.0) * 0.10)
        final_compute_output = base_compute_output * (1 - throttling_penalty)

        return {
            "outlet_temp_c": outlet_temp_c, "temp_deviation_c": temp_deviation_c, "cooling_strategy": strategy,
            "calculated_server_power_watts": server_power_watts, "cooling_unit_power_watts": cooling_unit_power_watts,
            "calculated_pue": pue, "compute_output": final_compute_output
        }

_twin_engine_instance = DataCenterTwin()
def compute_results(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _twin_engine_instance.compute_results(payload)

