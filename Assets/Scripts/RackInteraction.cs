using UnityEngine;
using UnityEngine.InputSystem;

public class RackInteraction : MonoBehaviour
{
    public Camera mainCamera;
    private RackInfo selectedRack;
    private bool showDetails = false;
    
    // UI Settings
    private Rect windowRect = new Rect(20, 20, 250, 150);

    void Start()
    {
        if (mainCamera == null) mainCamera = Camera.main;
    }

    void Update()
    {
        // Check for mouse click using the new Input System
        if (Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame)
        {
            Vector2 mousePos = Mouse.current.position.ReadValue();
            Ray ray = mainCamera.ScreenPointToRay(mousePos);
            RaycastHit hit;

            if (Physics.Raycast(ray, out hit))
            {
                RackInfo info = hit.collider.GetComponent<RackInfo>();
                if (info != null)
                {
                    selectedRack = info;
                    showDetails = true;
                }
                else
                {
                    // Clicked elsewhere, close details
                    showDetails = false;
                    selectedRack = null;
                }
            }
        }
    }

    void OnGUI()
    {
        if (showDetails && selectedRack != null)
        {
            windowRect = GUI.Window(0, windowRect, DrawWindow, "Rack Details");
        }
    }

    void DrawWindow(int windowID)
    {
        GUILayout.BeginVertical();
        GUILayout.Label($"ID: {selectedRack.rackId}");
        GUILayout.Label($"Index: {selectedRack.index}");
        GUILayout.Space(10);
        GUILayout.Label($"Temperature: {selectedRack.temperature:F2} °C");
        GUILayout.Label($"Energy Usage: {selectedRack.energy_usage:F2} kW");
        GUILayout.Label($"Status: {selectedRack.status}");
        
        GUILayout.Space(10);
        if (GUILayout.Button("Close"))
        {
            showDetails = false;
            selectedRack = null;
        }
        GUILayout.EndVertical();
        
        GUI.DragWindow();
    }
}
