using UnityEngine;
using System.Collections.Generic;

[ExecuteAlways]
public class RoomGenerator : MonoBehaviour
{
    public float width = 10f;
    public float depth = 10f;
    public float height = 75f; // Increased height
    public float wallThickness = 0.5f;
    public GameObject serverRackModel;
    public Vector3 rackPosition = new Vector3(0, 1f, 0); 
    public Vector3 rackRotation = new Vector3(-90, 180, 0);
    
    public int numberOfRacks = 175;
    public float rackSpacing = 2.5f;
    public float padding = 5f;
    
    public float lightIntensity = 100000f; // Very bright for HDRP
    public bool enableShadows = false; // Disable shadows for FPS

    public int numberOfFloors = 4; // Total floors
    List<GameObject> structuralObjects = new List<GameObject>(); // Track walls/floors for combining

    // GPU Instancing Data
    // GPU Instancing Data
    class InstancedMesh
    {
        public Mesh mesh;
        public Material material;
        // Key: Color Index (0-Steps), Value: List of matrices for that color
        public Dictionary<int, List<Matrix4x4>> colorBatches = new Dictionary<int, List<Matrix4x4>>();
    }

    struct RackInstance
    {
        public int index;
        public Matrix4x4[] partMatrices; // One matrix per mesh filter in the prefab
    }
    
    List<InstancedMesh> instancedMeshes = new List<InstancedMesh>();
    List<RackInstance> allRacks = new List<RackInstance>();
    
    // Quantization settings
    // Quantization settings
    [Range(2, 100)]
    public int colorSteps = 20; // Default to Low Quality
    
    [Tooltip("Distance beyond which racks are not rendered")]
    public float cullingDistance = 40f; // Culling Distance

    private MaterialPropertyBlock sharedBlock;
    private HeatmapManager heatmapManager;
    private List<Matrix4x4> visibleMatrices = new List<Matrix4x4>(); // Buffer for culling

    public void SetShadows(bool enabled)
    {
        enableShadows = enabled;
        Light[] lights = GetComponentsInChildren<Light>();
        foreach (var l in lights)
        {
            l.shadows = enabled ? LightShadows.Soft : LightShadows.None;
        }
    }

    void Start()
    {
        // Set Target FPS
        QualitySettings.vSyncCount = 0;
        Application.targetFrameRate = 60; // Increased to 60 FPS as requested
        
        // Ensure CameraManager is present
        if (GetComponent<CameraManager>() == null)
        {
            gameObject.AddComponent<CameraManager>();
        }
        
        // Ensure HeatmapManager is present
        heatmapManager = GetComponent<HeatmapManager>();
        if (heatmapManager == null)
        {
            heatmapManager = gameObject.AddComponent<HeatmapManager>();
        }

        // Ensure RackInteraction is present
        if (GetComponent<RackInteraction>() == null)
        {
            gameObject.AddComponent<RackInteraction>();
        }

        if (Application.isPlaying || instancedMeshes.Count == 0)
        {
            GenerateRoom();
        }
    }
    
    public bool showRacksInEditor = false; // Toggle to see racks in Edit Mode

    void Update()
    {
        // Only draw in Play Mode OR if explicitly enabled for Editor
        if (!Application.isPlaying && !showRacksInEditor) return;

        // Check Heatmap Toggle
        bool showHeatmap = false;
        if (heatmapManager == null) heatmapManager = GetComponent<HeatmapManager>();
        if (heatmapManager != null) showHeatmap = heatmapManager.useHeatmap;

        if (sharedBlock == null) sharedBlock = new MaterialPropertyBlock();

        // Render Racks using GPU Instancing with Color Batches
        Vector3 camPos = Camera.main ? Camera.main.transform.position : Vector3.zero;
        float sqrCullingDist = cullingDistance * cullingDistance;

        foreach (var item in instancedMeshes)
        {
            foreach (var batch in item.colorBatches)
            {
                int colorIndex = batch.Key;
                List<Matrix4x4> matrices = batch.Value;

                // CULLING LOGIC: Filter matrices based on distance
                visibleMatrices.Clear();
                for (int m = 0; m < matrices.Count; m++)
                {
                    Matrix4x4 mat = matrices[m];
                    // Extract position from matrix (Column 3)
                    Vector3 pos = new Vector3(mat.m03, mat.m13, mat.m23);
                    
                    if (Vector3.SqrMagnitude(pos - camPos) < sqrCullingDist)
                    {
                        visibleMatrices.Add(mat);
                    }
                }

                if (visibleMatrices.Count == 0) continue;

                if (showHeatmap && heatmapManager != null)
                {
                    // Calculate Color for this batch
                    float t = (float)colorIndex / (float)(colorSteps - 1);
                    Color batchColor = heatmapManager.heatmapGradient.Evaluate(t) * heatmapManager.heatmapIntensity;

                    // Set Property Block
                    sharedBlock.SetColor("_BaseColor", batchColor);
                    sharedBlock.SetColor("_EmissiveColor", batchColor);
                    sharedBlock.SetColor("_Color", batchColor);
                    sharedBlock.SetColor("_EmissionColor", batchColor);
                }
                else
                {
                    // Restore original state by clearing the block
                    // This tells the GPU to use the material's default properties
                    sharedBlock.Clear();
                }

                // Draw Batches (split if > 1023)
                for (int i = 0; i < visibleMatrices.Count; i += 1023)
                {
                    int count = Mathf.Min(1023, visibleMatrices.Count - i);
                    Graphics.DrawMeshInstanced(item.mesh, 0, item.material, visibleMatrices.GetRange(i, count), sharedBlock);
                }
            }
        }
    }

    [ContextMenu("Generate Room")]
    public void GenerateRoom()
    {
        // Ensure CameraManager is present
        if (GetComponent<CameraManager>() == null)
        {
            gameObject.AddComponent<CameraManager>();
        }
        
        // Ensure HeatmapManager is present
        HeatmapManager hm = GetComponent<HeatmapManager>();
        if (hm == null)
        {
            hm = gameObject.AddComponent<HeatmapManager>();
        }

        // Clear existing children
        while (transform.childCount > 0)
        {
            DestroyImmediate(transform.GetChild(0).gameObject);
        }
        
        // Clear lists
        structuralObjects.Clear();
        instancedMeshes.Clear();
        
        // Reset parent mesh if it exists
        if (GetComponent<MeshFilter>()) DestroyImmediate(GetComponent<MeshFilter>());
        if (GetComponent<MeshRenderer>()) DestroyImmediate(GetComponent<MeshRenderer>());
        
        // Calculate grid dimensions
        int columns = Mathf.CeilToInt(Mathf.Sqrt(numberOfRacks));
        int rows = Mathf.CeilToInt((float)numberOfRacks / columns);

        // Calculate room size
        float calculatedWidth = (columns - 1) * rackSpacing + padding * 2;
        float calculatedDepth = (rows - 1) * rackSpacing + padding * 2;
        
        width = Mathf.Max(calculatedWidth, 10f);
        depth = Mathf.Max(calculatedDepth, 10f);

        // Create the material
        Shader wallShader = Shader.Find("HDRP/Lit");
        if (wallShader == null) wallShader = Shader.Find("Standard");
        if (wallShader == null) wallShader = Shader.Find("Legacy Shaders/Diffuse"); // Ultimate fallback
        
        Material wallMaterial;
        if (wallShader != null)
        {
            wallMaterial = new Material(wallShader);
        }
        else
        {
            // If absolutely no shader found, use a default material (pink but won't crash)
            wallMaterial = new Material(Shader.Find("Hidden/InternalErrorShader")); 
            if (wallMaterial.shader == null) wallMaterial = new Material(Shader.Find("Standard")); // Try again just in case
        }
        
        // Instancing not strictly needed for GameObjects but good for batching if static
        wallMaterial.enableInstancing = true; 
        
        Color wallColor;
        ColorUtility.TryParseHtmlString("#494949", out wallColor);
        
        if (wallMaterial.HasProperty("_BaseColor"))
        {
            wallMaterial.SetColor("_BaseColor", wallColor);
        }
        else
        {
            wallMaterial.color = wallColor;
        }

        // Create Emissive Material (Shared)
        Shader lightShader = Shader.Find("HDRP/Lit");
        if (lightShader == null) lightShader = Shader.Find("Standard");
        
        Material lightMat;
        if (lightShader != null) lightMat = new Material(lightShader);
        else lightMat = new Material(Shader.Find("Legacy Shaders/Self-Illumin/VertexLit"));

        if (lightMat.HasProperty("_EmissiveColor"))
        {
            lightMat.SetColor("_BaseColor", Color.white);
            lightMat.SetColor("_EmissiveColor", Color.white * 10000f); // High intensity for HDRP
            lightMat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
        }
        else
        {
            lightMat.EnableKeyword("_EMISSION");
            lightMat.SetColor("_EmissionColor", Color.white);
        }

        // Define Light Positions (Optimized: 1 Central Light)
        Vector3[] lightPositions = new Vector3[]
        {
            new Vector3(0, 0, 0), // Center only
        };

        // Generate Base Floor
        // Extended to cover the walls and the corner gap
        CreateWall("Floor_Base", new Vector3(width + wallThickness, wallThickness, depth + wallThickness), new Vector3(-wallThickness / 2, -wallThickness / 2, wallThickness / 2), wallMaterial);

        // Loop for each floor
        for (int i = 0; i < numberOfFloors; i++)
        {
            // Fix Collision: Add wallThickness to the height offset
            float currentFloorY = i * (height + wallThickness);
            string floorSuffix = $"_Level{i}";

            // Walls
            // Back Wall
            CreateWall("BackWall" + floorSuffix, new Vector3(width, height, wallThickness), new Vector3(0, currentFloorY + height / 2, (depth / 2) + (wallThickness / 2)), wallMaterial);
            // Left Wall
            CreateWall("LeftWall" + floorSuffix, new Vector3(wallThickness, height, depth), new Vector3(-(width / 2) - (wallThickness / 2), currentFloorY + height / 2, 0), wallMaterial);
            
            // Corner Pillar (Fills the gap between Left and Back walls)
            CreateWall("CornerPillar" + floorSuffix, new Vector3(wallThickness, height, wallThickness), new Vector3(-(width / 2) - (wallThickness / 2), currentFloorY + height / 2, (depth / 2) + (wallThickness / 2)), wallMaterial);

            // Ceiling / Roof for this level
            // Extended to cover the walls and the corner gap
            // New Size: width + wallThickness, depth + wallThickness
            // New Center: shifted by -wallThickness/2 in X and +wallThickness/2 in Z
            CreateWall("Roof" + floorSuffix, new Vector3(width + wallThickness, wallThickness, depth + wallThickness), new Vector3(-wallThickness / 2, currentFloorY + height + (wallThickness / 2), wallThickness / 2), wallMaterial);

            // Lights for this level - OPTIMIZATION: Skip lights on the top floor (Roof) or reduce count
            // Also, strictly disable shadows
            if (i < numberOfFloors - 1) // Don't generate lights for the very top roof if not needed
            {
                GenerateLights(lightPositions, currentFloorY + height, lightMat);
            }

            // Racks for this level (Proxies + Data Prep)
            if (serverRackModel != null)
            {
                CreateRackProxies(columns, rows, currentFloorY);
            }
        }
        
        // Prepare Instancing Data for ALL racks across all floors
        if (serverRackModel != null)
        {
            PrepareInstancingData(columns, rows);
        }

        // Combine Meshes (Only structural ones)
        CombineRoomMeshes(wallMaterial);
    }
    
    // ... (Existing code)

    public void UpdateRackVisuals(List<RackData> racks, Color[] colors)
    {
        // 1. Clear existing batches
        foreach (var item in instancedMeshes)
        {
            item.colorBatches.Clear();
        }

        // 2. Rebuild batches based on temperature/color
        if (heatmapManager == null) heatmapManager = GetComponent<HeatmapManager>();
        
        float minTemp = heatmapManager != null ? heatmapManager.minTemp : 20f;
        float maxTemp = heatmapManager != null ? heatmapManager.maxTemp : 45f;

        // Create a map of rackId -> RackData for faster lookup if needed, 
        // but here we assume list order matches if indices are aligned.
        // Better: use the 'racks' list directly if it matches 'allRacks' count.
        // If 'racks' is null (init), put everything in one batch (e.g. index 0).

        for (int i = 0; i < allRacks.Count; i++)
        {
            RackInstance rackInstance = allRacks[i];
            int colorIndex = 0; // Default

            if (racks != null && i < racks.Count)
            {
                // Find data for this rack. 
                // Assuming racks list is sorted or matches index. 
                // If not, we should use a Dictionary lookup.
                // For performance, let's assume index matching for now or simple lookup.
                // Given the previous code used index matching, we stick to it.
                
                // Safety check
                if (i < racks.Count)
                {
                    float temp = racks[i].temperature;
                    float t = Mathf.InverseLerp(minTemp, maxTemp, temp);
                    colorIndex = Mathf.Clamp(Mathf.FloorToInt(t * (colorSteps - 1)), 0, colorSteps - 1);
                }
            }

            // Add to batches for each mesh part
            for (int m = 0; m < instancedMeshes.Count; m++)
            {
                InstancedMesh im = instancedMeshes[m];
                if (!im.colorBatches.ContainsKey(colorIndex))
                {
                    im.colorBatches[colorIndex] = new List<Matrix4x4>();
                }
                im.colorBatches[colorIndex].Add(rackInstance.partMatrices[m]);
            }
        }

        // 3. Update Proxy Data (for Interaction)
        if (racks != null)
        {
            RackInfo[] proxies = GetComponentsInChildren<RackInfo>();
            foreach (var proxy in proxies)
            {
                // Find data for this proxy
                // Assuming proxy.index corresponds to racks list index
                if (proxy.index < racks.Count)
                {
                    RackData data = racks[proxy.index];
                    proxy.rackId = data.id;
                    proxy.temperature = data.temperature;
                    proxy.energy_usage = data.energy_usage;
                    proxy.status = data.status;
                }
            }
        }
    }
    
    void CreateRackProxies(int columns, int rows, float yOffset)
    {
        float gridWidth = (columns - 1) * rackSpacing;
        float gridDepth = (rows - 1) * rackSpacing;
        float startX = -gridWidth / 2;
        float startZ = -gridDepth / 2; 
        
        // Get bounds from the model to size the collider correctly
        Bounds bounds = new Bounds(Vector3.zero, Vector3.one);
        Renderer[] renderers = serverRackModel.GetComponentsInChildren<Renderer>();
        if (renderers.Length > 0)
        {
            bounds = renderers[0].bounds;
            for (int i = 1; i < renderers.Length; i++)
                bounds.Encapsulate(renderers[i].bounds);
        }
        // Adjust bounds to local space roughly
        Vector3 colliderSize = bounds.size;
        // Default fallback if bounds are tiny/zero
        if (colliderSize.magnitude < 0.1f) colliderSize = new Vector3(1, 2, 1);

        for (int i = 0; i < numberOfRacks; i++)
        {
            int row = i / columns;
            int col = i % columns;

            float xPos = startX + (col * rackSpacing);
            float zPos = startZ + (row * rackSpacing);

            Vector3 pos = new Vector3(xPos, rackPosition.y + yOffset, zPos);
            
            // Create Empty GameObject
            GameObject proxy = new GameObject($"ServerRack_L{Mathf.RoundToInt(yOffset/height)}_{i}");
            proxy.transform.parent = transform;
            proxy.transform.localPosition = pos;
            proxy.transform.localRotation = Quaternion.Euler(rackRotation);
            
            // Add Collider
            BoxCollider bc = proxy.AddComponent<BoxCollider>();
            bc.size = colliderSize;
            bc.center = bounds.center; // Approximate center

            // Add RackInfo
            RackInfo info = proxy.AddComponent<RackInfo>();
            info.index = i + (Mathf.RoundToInt(yOffset / (height + wallThickness)) * numberOfRacks); // Global Index
            info.rackId = $"Rack_{info.index}";
        }
    }
    
    // ... (Rest of existing code)
    
    void PrepareInstancingData(int columns, int rows)
    {
        instancedMeshes.Clear();
        allRacks.Clear();

        // 1. Extract Meshes and Materials from the Prefab
        MeshFilter[] meshFilters = serverRackModel.GetComponentsInChildren<MeshFilter>();
        
        // Cache to preserve batching while ensuring instancing is enabled
        Dictionary<Material, Material> instancedMaterials = new Dictionary<Material, Material>();
        
        // Initialize InstancedMesh objects
        foreach (MeshFilter mf in meshFilters)
        {
            Mesh mesh = mf.sharedMesh;
            Renderer renderer = mf.GetComponent<Renderer>();
            
            if (mesh == null || renderer == null || renderer.sharedMaterial == null) continue;
            
            Material originalMat = renderer.sharedMaterial;
            Material mat;

            if (instancedMaterials.ContainsKey(originalMat))
            {
                mat = instancedMaterials[originalMat];
            }
            else
            {
                mat = new Material(originalMat);
                mat.enableInstancing = true;
                instancedMaterials[originalMat] = mat;
            }

            InstancedMesh instancedMesh = new InstancedMesh();
            instancedMesh.mesh = mesh;
            instancedMesh.material = mat;
            instancedMeshes.Add(instancedMesh);
        }

        float gridWidth = (columns - 1) * rackSpacing;
        float gridDepth = (rows - 1) * rackSpacing;
        float startX = -gridWidth / 2;
        float startZ = -gridDepth / 2; 

        int globalRackIndex = 0;

        // 2. Create Rack Instances (Geometry Data)
        for (int floor = 0; floor < numberOfFloors; floor++)
        {
            float yOffset = floor * (height + wallThickness);
            
            for (int i = 0; i < numberOfRacks; i++)
            {
                int row = i / columns;
                int col = i % columns;

                float xPos = startX + (col * rackSpacing);
                float zPos = startZ + (row * rackSpacing);

                Vector3 pos = new Vector3(xPos, rackPosition.y + yOffset, zPos);
                
                // Create RackInstance
                RackInstance rack = new RackInstance();
                rack.index = globalRackIndex;
                rack.partMatrices = new Matrix4x4[instancedMeshes.Count];

                // Calculate matrices for each part
                int meshIndex = 0;
                foreach (MeshFilter mf in meshFilters)
                {
                    Renderer renderer = mf.GetComponent<Renderer>();
                    if (mf.sharedMesh == null || renderer == null || renderer.sharedMaterial == null) continue;

                    // Calculate local transformation relative to the RoomGenerator
                    Matrix4x4 meshLocalMatrix = Matrix4x4.TRS(mf.transform.localPosition, mf.transform.localRotation, mf.transform.localScale);
                    Matrix4x4 rackInstanceMatrix = Matrix4x4.TRS(pos, Quaternion.Euler(rackRotation), Vector3.one);
                    
                    // Combined Local Matrix (Mesh -> Room)
                    Matrix4x4 finalLocalMatrix = rackInstanceMatrix * meshLocalMatrix;
                    
                    // Convert to World Matrix (Assuming static room for max performance)
                    Matrix4x4 finalWorldMatrix = transform.localToWorldMatrix * finalLocalMatrix;
                    
                    rack.partMatrices[meshIndex] = finalWorldMatrix;
                    meshIndex++;
                }

                allRacks.Add(rack);
                globalRackIndex++;
            }
        }
        
        // Initial visual update (default white)
        UpdateRackVisuals(null, null);
    }

    void CreateWall(string name, Vector3 scale, Vector3 position, Material mat)
    {
        GameObject wall = GameObject.CreatePrimitive(PrimitiveType.Cube);
        wall.name = name;
        wall.transform.parent = this.transform;
        wall.transform.localScale = scale;
        wall.transform.localPosition = position;
        
        Renderer renderer = wall.GetComponent<Renderer>();
        if (renderer != null)
        {
            renderer.material = mat;
        }
        
        // Add to structural list for combining later
        structuralObjects.Add(wall);
    }

    void CombineRoomMeshes(Material mat)
    {
        // Combine only the objects we explicitly tracked as structural
        if (structuralObjects.Count == 0) return;

        CombineInstance[] combine = new CombineInstance[structuralObjects.Count];

        int i = 0;
        foreach (GameObject obj in structuralObjects)
        {
            MeshFilter mf = obj.GetComponent<MeshFilter>();
            if (mf != null)
            {
                combine[i].mesh = mf.sharedMesh;
                combine[i].transform = mf.transform.localToWorldMatrix;
                // Disable the original renderer
                obj.SetActive(false);
            }
            i++;
        }

        // Add MeshFilter and Renderer to parent if not present
        MeshFilter parentMf = gameObject.GetComponent<MeshFilter>();
        if (!parentMf) parentMf = gameObject.AddComponent<MeshFilter>();
        
        MeshRenderer parentMr = gameObject.GetComponent<MeshRenderer>();
        if (!parentMr) parentMr = gameObject.AddComponent<MeshRenderer>();

        Mesh combinedMesh = new Mesh();
        combinedMesh.name = "CombinedRoom";
        
        // Re-calculate combine instances relative to parent for the final mesh
        i = 0;
        foreach (GameObject obj in structuralObjects)
        {
            MeshFilter mf = obj.GetComponent<MeshFilter>();
            if (mf != null)
            {
                combine[i].mesh = mf.sharedMesh;
                combine[i].transform = transform.worldToLocalMatrix * mf.transform.localToWorldMatrix;
            }
            i++;
        }

        combinedMesh.CombineMeshes(combine);
        parentMf.sharedMesh = combinedMesh;
        parentMr.material = mat;
        parentMr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.TwoSided;
        
        // Static batching for the combined mesh
        gameObject.isStatic = true;

        // Destroy the temporary wall objects
        foreach (GameObject obj in structuralObjects)
        {
            DestroyImmediate(obj);
        }
        structuralObjects.Clear();
    }


    void GenerateLights(Vector3[] lightPositions, float ceilingHeight, Material lightMat)
    {
        foreach (Vector3 pos in lightPositions)
        {
            // Add Light Fixture (Visual)
            GameObject lightFixture = GameObject.CreatePrimitive(PrimitiveType.Cube);
            lightFixture.name = "LightFixture";
            lightFixture.transform.parent = this.transform;
            lightFixture.transform.localPosition = new Vector3(pos.x, ceilingHeight - 0.1f, pos.z); // At ceiling
            lightFixture.transform.localScale = new Vector3(5f, 0.2f, 5f); // Large Panel
            
            Renderer fixtureRenderer = lightFixture.GetComponent<Renderer>();
            if (fixtureRenderer) fixtureRenderer.material = lightMat;

            // Add Light Source
            GameObject lightObj = new GameObject("RoomLight");
            lightObj.transform.parent = this.transform;
            lightObj.transform.localPosition = new Vector3(pos.x, ceilingHeight - 1f, pos.z);
            lightObj.transform.localRotation = Quaternion.Euler(90, 0, 0); 
            Light lightComp = lightObj.AddComponent<Light>();
            lightComp.type = LightType.Spot;
            lightComp.spotAngle = 170f;
            lightComp.range = Mathf.Max(width, depth) * 1.5f; 
            lightComp.intensity = lightIntensity; 
            lightComp.color = Color.white;
            
            if (enableShadows) lightComp.shadows = LightShadows.Soft;
            else lightComp.shadows = LightShadows.None;
        }
    }
}
