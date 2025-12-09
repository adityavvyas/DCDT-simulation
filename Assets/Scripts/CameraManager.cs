using UnityEngine;
using UnityEngine.Rendering;

[ExecuteAlways]
public class CameraManager : MonoBehaviour
{
    void Update()
    {
        Camera cam = Camera.main;
        if (cam == null)
        {
            cam = FindFirstObjectByType<Camera>();
        }

        if (cam != null)
        {
            // Check for HDAdditionalCameraData using reflection to avoid hard dependency errors if package is missing
            var hdData = cam.GetComponent("HDAdditionalCameraData");
            if (hdData == null)
            {
                System.Type hdType = System.Type.GetType("UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData, Unity.RenderPipelines.HighDefinition.Runtime");
                if (hdType != null)
                {
                    cam.gameObject.AddComponent(hdType);
                }
            }

            // Ensure FreeCamera is attached for navigation
            if (cam.GetComponent<FreeCamera>() == null)
            {
                cam.gameObject.AddComponent<FreeCamera>();
            }

            // Ensure SimulationUI is attached for metrics
            if (cam.GetComponent<SimulationUI>() == null)
            {
                cam.gameObject.AddComponent<SimulationUI>();
            }
        }
    }
}
