using System;
using System.Collections.Generic;

[Serializable]
public class RackData
{
    public string id;
    public int index; // Index in the flat list, useful for mapping to instanced mesh instances
    public float temperature; // Value between 0 and 1 (or actual temp to be normalized)
    public float energy_usage;
    public string status; // "Normal", "Warning", "Critical"
}

[Serializable]
public class SimulationState
{
    public List<RackData> racks;
    public float timestamp;
    
    // Global Metrics
    public float total_server_power;
    public float total_cooling_power;
    public float average_pue;
    public float max_outlet_temp;
    public float total_compute_output;
    public float projected_daily_cost;
    public string cooling_strategy;
}
