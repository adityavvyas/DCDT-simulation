using UnityEngine;
using System.Collections.Generic;

[ExecuteAlways]
public class HeatmapManager : MonoBehaviour
{
    [Header("Heatmap Settings")]
    public bool useHeatmap = true;
    public Gradient heatmapGradient;
    [Range(0f, 1f)]
    public float heatmapIntensity = 1.0f; // Intensity of the color on the model

    // Min/Max for normalization (matching the gradient keys above)
    public float minTemp = 20.0f;
    public float maxTemp = 45.0f;

    private WebSocketConnector connector;

    void Start()
    {
        // Initialize Gradient to match Python UI
        // Range: 20C to 45C
        heatmapGradient = new Gradient();
        
        // Python Color Map:
        // 20.0: Dark Blue (0, 0, 139)
        // 27.0: Green (0, 128, 0)
        // 32.0: Yellow (255, 255, 0)
        // 36.0: Orange (255, 165, 0)
        // 39.0: Red (255, 0, 0)
        // 45.0: Dark Red (139, 0, 0)

        GradientColorKey[] colorKeys = new GradientColorKey[6];
        colorKeys[0] = new GradientColorKey(new Color(0, 0, 139f/255f), 0.0f);   // 20C (0%)
        colorKeys[1] = new GradientColorKey(new Color(0, 128f/255f, 0), 0.28f);  // 27C (28%)
        colorKeys[2] = new GradientColorKey(Color.yellow, 0.48f);                // 32C (48%)
        colorKeys[3] = new GradientColorKey(new Color(1f, 165f/255f, 0), 0.64f); // 36C (64%)
        colorKeys[4] = new GradientColorKey(Color.red, 0.76f);                   // 39C (76%)
        colorKeys[5] = new GradientColorKey(new Color(139f/255f, 0, 0), 1.0f);   // 45C (100%)

        GradientAlphaKey[] alphaKeys = new GradientAlphaKey[2];
        alphaKeys[0] = new GradientAlphaKey(1.0f, 0.0f);
        alphaKeys[1] = new GradientAlphaKey(1.0f, 1.0f);

        heatmapGradient.SetKeys(colorKeys, alphaKeys);

        connector = GetComponent<WebSocketConnector>();
        if (connector == null) connector = gameObject.AddComponent<WebSocketConnector>();
        
        connector.OnSimulationStateReceived += OnDataReceived;
    }

    private void OnDataReceived(SimulationState state)
    {
        if (!useHeatmap || state == null || state.racks == null) return;

        Color[] newColors = new Color[state.racks.Count];

        for (int i = 0; i < state.racks.Count; i++)
        {
            // Normalize temperature to 0-1 range for gradient evaluation
            float temp = state.racks[i].temperature;
            float t = Mathf.InverseLerp(minTemp, maxTemp, temp);
            
            newColors[i] = heatmapGradient.Evaluate(t) * heatmapIntensity;
        }

        // Notify RoomGenerator
        RoomGenerator roomGen = GetComponent<RoomGenerator>();
        if (roomGen != null)
        {
            roomGen.UpdateRackVisuals(state.racks, newColors);
        }
    }

    // Fallback for random generation if needed
    public Color[] GenerateHeatmapColors(int count)
    {
        Color[] colors = new Color[count];
        for (int i = 0; i < count; i++)
        {
            float heatValue = Random.Range(0f, 1f);
            Color c = heatmapGradient.Evaluate(heatValue);
            colors[i] = c * heatmapIntensity; 
        }
        return colors;
    }
}
