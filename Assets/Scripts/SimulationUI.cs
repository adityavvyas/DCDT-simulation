using UnityEngine;
using System.Linq;

public class SimulationUI : MonoBehaviour
{
    private SimulationState currentState;
    private WebSocketConnector connector;
    private RoomGenerator roomGenerator;
    private HeatmapManager heatmapManager;

    void Start()
    {
        // Ensure we start in Windowed mode to allow resizing/split-screen
        Screen.fullScreen = false;
        Screen.fullScreenMode = FullScreenMode.Windowed;

        connector = FindFirstObjectByType<WebSocketConnector>();
        if (connector != null)
        {
            connector.OnSimulationStateReceived += OnDataReceived;
        }
        
        roomGenerator = FindFirstObjectByType<RoomGenerator>();
        heatmapManager = FindFirstObjectByType<HeatmapManager>();
    }

    private float nextUpdate = 0f;
    private float updateInterval = 0.25f; // Update UI 4 times per second

    void OnDataReceived(SimulationState state)
    {
        currentState = state;
    }

    void Update()
    {
        if (Time.time >= nextUpdate)
        {
            CalculateMetrics();
            nextUpdate = Time.time + updateInterval;
        }
    }

    void CalculateMetrics()
    {
        if (currentState == null || currentState.racks == null || currentState.racks.Count == 0) return;

        float powerSum = 0f;
        float tempSum = 0f;
        float maxT = float.MinValue;
        int critical = 0;
        int warning = 0;

        foreach (var rack in currentState.racks)
        {
            powerSum += rack.energy_usage;
            
            float t = rack.temperature;
            if (t > maxT) maxT = t;
            tempSum += t;

            if (rack.status == "Critical") critical++;
            if (rack.status == "Warning") warning++;
        }

        // 1. Server Power (Always calculate from sum to be safe)
        // Convert Watts to Kilowatts (assuming raw data is in Watts)
        currentState.total_server_power = powerSum / 1000f;

        // 2. Temperatures
        currentState.max_outlet_temp = maxT;
        float avgTemp = tempSum / currentState.racks.Count;

        // 3. PUE (Estimate if missing)
        // Logic: Base 1.2 + penalty for high average temp
        if (currentState.average_pue == 0)
        {
            float tempPenalty = Mathf.Max(0, avgTemp - 20f) * 0.03f;
            currentState.average_pue = 1.2f + tempPenalty;
        }

        // 4. Cooling Power (Estimate if missing)
        // Logic: ServerPower * (PUE - 1)
        if (currentState.total_cooling_power == 0)
        {
            currentState.total_cooling_power = currentState.total_server_power * (currentState.average_pue - 1f);
        }

        // 5. Compute Output (Estimate if missing)
        // Logic: Arbitrary scale based on power (approx 6000 ops per kW)
        if (currentState.total_compute_output == 0)
        {
            currentState.total_compute_output = currentState.total_server_power * 6000f; 
        }

        // 6. Daily Cost (Estimate if missing)
        // Logic: Total Power * 24h * $0.12/kWh
        if (currentState.projected_daily_cost == 0)
        {
            float totalPower = currentState.total_server_power + currentState.total_cooling_power;
            currentState.projected_daily_cost = totalPower * 24f * 0.12f;
        }

        // 7. Strategy
        if (string.IsNullOrEmpty(currentState.cooling_strategy))
        {
            if (critical > 0)
            {
                currentState.cooling_strategy = "CRITICAL: Boost All Cooling";
            }
            else if (warning > 5)
            {
                currentState.cooling_strategy = "Warning: Increase Airflow";
            }
            else
            {
                currentState.cooling_strategy = "Optimized (Eco Mode)";
            }
        }
    }

    void OnGUI()
    {
        // SCALING LOGIC: Responsive "Match Width Or Height"
        float refWidth = 1920f;
        float refHeight = 1080f;
        
        float scaleX = Screen.width / refWidth;
        float scaleY = Screen.height / refHeight;
        
        // Use the smaller scale to ensure UI fits in both dimensions (Split Screen support)
        float scale = Mathf.Min(scaleX, scaleY);
        
        // Enforce a minimum scale for readability
        scale = Mathf.Max(scale, 0.4f);

        Matrix4x4 oldMatrix = GUI.matrix;
        GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(scale, scale, 1));

        // Calculate effective screen width in the scaled space
        float effectiveScreenWidth = Screen.width / scale;

        float width = 450;
        float padding = 20;
        float x = effectiveScreenWidth - width - padding;
        float y = padding;
        float height = 550;

        // Dark Background
        GUI.Box(new Rect(x, y, width, height), "");
        GUI.Box(new Rect(x, y, width, height), ""); // Double box for darker opacity if using default skin

        GUILayout.BeginArea(new Rect(x + 15, y + 15, width - 30, height - 30));

        // Header
        GUIStyle headerStyle = new GUIStyle(GUI.skin.label);
        headerStyle.fontSize = 18;
        headerStyle.fontStyle = FontStyle.Bold;
        headerStyle.normal.textColor = new Color(0.4f, 0.6f, 1f); // Light Blue
        GUILayout.Label("Current Metrics", headerStyle);
        GUILayout.Space(15);

        if (currentState != null)
        {
            DrawMetricRow("Total Server Power (kW)", $"{currentState.total_server_power:F1} kW", false);
            DrawMetricRow("Total Cooling Power (kW)", $"{currentState.total_cooling_power:F1} kW", false);
            DrawMetricRow("Average PUE", $"{currentState.average_pue:F2}", currentState.average_pue > 1.5f);
            DrawMetricRow("MAX Outlet Temp (°C)", $"{currentState.max_outlet_temp:F1} °C", currentState.max_outlet_temp > 40f);
            DrawMetricRow("Total Compute Output", $"{currentState.total_compute_output:N0}", false);
            DrawMetricRow("Projected Daily Cost (USD)", $"${currentState.projected_daily_cost:N0}", false);
            
            GUILayout.Space(10);
            
            // Cooling Strategy
            GUILayout.BeginHorizontal();
            GUIStyle labelStyle = new GUIStyle(GUI.skin.label) { fontSize = 14, fontStyle = FontStyle.Bold };
            GUILayout.Label("Cooling Strategy", labelStyle, GUILayout.Width(180));
            
            GUIStyle strategyStyle = new GUIStyle(GUI.skin.label) { fontSize = 14, fontStyle = FontStyle.Bold };
            if (currentState.cooling_strategy != null && currentState.cooling_strategy.ToUpper().Contains("CRITICAL"))
            {
                strategyStyle.normal.textColor = Color.red;
            }
            else
            {
                strategyStyle.normal.textColor = Color.green;
            }
            GUILayout.Label(currentState.cooling_strategy ?? "Optimized", strategyStyle);
            GUILayout.EndHorizontal();

            GUILayout.FlexibleSpace();
            GUILayout.Label($"Last Update: {System.DateTime.Now:HH:mm:ss}", new GUIStyle(GUI.skin.label) { fontSize = 10, alignment = TextAnchor.MiddleRight, normal = { textColor = Color.gray } });
        }
        else
        {
            GUILayout.FlexibleSpace();
            GUILayout.Label("Waiting for data...", new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontSize = 16 });
            GUILayout.Label("Press 'R' to Refresh Connection", new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontSize = 12, normal = { textColor = Color.gray } });
            GUILayout.FlexibleSpace();
        }

        GUILayout.Space(10);
        DrawSettings();

        GUILayout.EndArea();

        // Restore matrix
        GUI.matrix = oldMatrix;
    }

    void DrawSettings()
    {
        GUILayout.Label("Performance Settings", new GUIStyle(GUI.skin.label) { fontSize = 14, fontStyle = FontStyle.Bold, normal = { textColor = Color.yellow } });
        
        if (roomGenerator != null)
        {
            bool shadow = GUILayout.Toggle(roomGenerator.enableShadows, " Enable Shadows (Heavy)");
            if (shadow != roomGenerator.enableShadows)
            {
                roomGenerator.SetShadows(shadow);
            }
        }

        if (heatmapManager != null)
        {
            bool heatmap = GUILayout.Toggle(heatmapManager.useHeatmap, " Show Heatmap");
            if (heatmap != heatmapManager.useHeatmap)
            {
                heatmapManager.useHeatmap = heatmap;
            }
        }
    }

    void DrawMetricRow(string label, string value, bool isCritical)
    {
        GUILayout.BeginHorizontal();
        
        GUIStyle labelStyle = new GUIStyle(GUI.skin.label);
        labelStyle.fontSize = 14;
        labelStyle.normal.textColor = Color.white;
        GUILayout.Label(label, labelStyle, GUILayout.Width(200));

        GUIStyle valueStyle = new GUIStyle(GUI.skin.label);
        valueStyle.fontSize = 14;
        valueStyle.fontStyle = FontStyle.Bold;
        valueStyle.normal.textColor = Color.white;
        GUILayout.Label(value, valueStyle);

        if (isCritical)
        {
            GUIStyle alertStyle = new GUIStyle(GUI.skin.label);
            alertStyle.fontSize = 12;
            alertStyle.fontStyle = FontStyle.Bold;
            alertStyle.normal.textColor = new Color(1f, 0.3f, 0.3f); // Reddish
            alertStyle.alignment = TextAnchor.MiddleRight;
            GUILayout.Label("⚠ High", alertStyle, GUILayout.Width(60));
        }

        GUILayout.EndHorizontal();
        GUILayout.Space(5);
    }

    void OnDestroy()
    {
        if (connector != null)
        {
            connector.OnSimulationStateReceived -= OnDataReceived;
        }
    }
}
