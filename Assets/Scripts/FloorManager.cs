using UnityEngine;
using System.Collections.Generic;

public class FloorManager : MonoBehaviour
{
    public List<GameObject> floorRoots = new List<GameObject>();
    public float floorHeight = 75.5f; // Height + Thickness
    public Transform cameraTransform;
    
    private int currentFloorIndex = -1;

    void Start()
    {
        if (cameraTransform == null && Camera.main != null)
        {
            cameraTransform = Camera.main.transform;
        }
    }

    void Update()
    {
        if (cameraTransform == null) return;

        // Calculate which floor the camera is on
        // Assuming floor 0 is at y=0 to y=floorHeight
        float camY = cameraTransform.position.y;
        int newIndex = Mathf.FloorToInt(camY / floorHeight);
        
        // Clamp index
        newIndex = Mathf.Clamp(newIndex, 0, floorRoots.Count - 1);

        if (newIndex != currentFloorIndex)
        {
            SetActiveFloor(newIndex);
        }
    }

    public void RegisterFloor(GameObject floorRoot)
    {
        if (!floorRoots.Contains(floorRoot))
        {
            floorRoots.Add(floorRoot);
            // Hide by default if not the first one
            if (floorRoots.Count > 1)
            {
                floorRoot.SetActive(false);
            }
        }
    }

    public void ClearFloors()
    {
        floorRoots.Clear();
        currentFloorIndex = -1;
    }

    void SetActiveFloor(int index)
    {
        currentFloorIndex = index;
        
        for (int i = 0; i < floorRoots.Count; i++)
        {
            if (floorRoots[i] != null)
            {
                bool shouldBeActive = (i == index);
                if (floorRoots[i].activeSelf != shouldBeActive)
                {
                    floorRoots[i].SetActive(shouldBeActive);
                }
            }
        }
    }
}
