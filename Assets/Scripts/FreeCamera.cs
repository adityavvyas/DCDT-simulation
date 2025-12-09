using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

public class FreeCamera : MonoBehaviour
{
    [Header("Movement Settings")]
    public float movementSpeed = 10f;
    public float fastSpeedMultiplier = 5f;
    public float mouseSensitivity = 2f;
    public bool invertY = false; // Added Invert Y option

    private float rotationX = 0f;
    private float rotationY = 0f;

    void Start()
    {
        // Initialize rotation based on current camera rotation
        Vector3 angles = transform.eulerAngles;
        rotationX = angles.y;
        rotationY = angles.x;
    }

    void Update()
    {
        bool rightMousePressed = false;
        float mouseX = 0f;
        float mouseY = 0f;
        bool shiftPressed = false;
        Vector3 moveDirection = Vector3.zero;

#if ENABLE_INPUT_SYSTEM
        // New Input System
        if (Mouse.current != null)
        {
            rightMousePressed = Mouse.current.rightButton.isPressed;
            Vector2 delta = Mouse.current.delta.ReadValue();
            mouseX = delta.x * mouseSensitivity * 0.1f; 
            mouseY = delta.y * mouseSensitivity * 0.1f;
        }

        if (Keyboard.current != null)
        {
            shiftPressed = Keyboard.current.leftShiftKey.isPressed;
            if (Keyboard.current.wKey.isPressed) moveDirection += transform.forward;
            if (Keyboard.current.sKey.isPressed) moveDirection -= transform.forward;
            if (Keyboard.current.aKey.isPressed) moveDirection -= transform.right;
            if (Keyboard.current.dKey.isPressed) moveDirection += transform.right;
            if (Keyboard.current.jKey.isPressed) moveDirection += Vector3.up; // J for Up
            if (Keyboard.current.kKey.isPressed) moveDirection -= Vector3.up; // K for Down
            
            // Exit Application
            if (Keyboard.current.qKey.wasPressedThisFrame)
            {
                #if UNITY_EDITOR
                UnityEditor.EditorApplication.isPlaying = false;
                #else
                Application.Quit();
                #endif
            }

            // Toggle Fullscreen
            if (Keyboard.current.fKey.wasPressedThisFrame)
            {
                Screen.fullScreen = !Screen.fullScreen;
            }
        }
#else
        // Legacy Input System
        rightMousePressed = Input.GetMouseButton(1);
        mouseX = Input.GetAxis("Mouse X") * mouseSensitivity;
        mouseY = Input.GetAxis("Mouse Y") * mouseSensitivity;
        shiftPressed = Input.GetKey(KeyCode.LeftShift);

        if (Input.GetKey(KeyCode.W)) moveDirection += transform.forward;
        if (Input.GetKey(KeyCode.S)) moveDirection -= transform.forward;
        if (Input.GetKey(KeyCode.A)) moveDirection -= transform.right;
        if (Input.GetKey(KeyCode.D)) moveDirection += transform.right;
        if (Input.GetKey(KeyCode.J)) moveDirection += Vector3.up; // J for Up
        if (Input.GetKey(KeyCode.K)) moveDirection -= Vector3.up; // K for Down

        if (Input.GetKeyDown(KeyCode.Q))
        {
            #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
            #else
            Application.Quit();
            #endif
        }

        if (Input.GetKeyDown(KeyCode.F))
        {
            Screen.fullScreen = !Screen.fullScreen;
        }
#endif

        // 1. Rotation
        if (rightMousePressed)
        {
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;

            rotationX += mouseX;
            
            // Handle Invert Y
            if (invertY)
            {
                rotationY += mouseY;
            }
            else
            {
                rotationY -= mouseY;
            }
            
            rotationY = Mathf.Clamp(rotationY, -90f, 90f);

            transform.rotation = Quaternion.Euler(rotationY, rotationX, 0);
        }
        else
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }

        // 2. Movement
        float currentSpeed = movementSpeed;
        if (shiftPressed)
        {
            currentSpeed *= fastSpeedMultiplier;
        }

        transform.position += moveDirection * currentSpeed * Time.deltaTime;
    }

    void OnGUI()
    {
        GUI.color = Color.black;
        GUI.Label(new Rect(10, 10, 300, 20), $"Camera Pos: {transform.position}");
        GUI.Label(new Rect(10, 30, 300, 20), $"Camera Rot: {transform.eulerAngles}");
        GUI.Label(new Rect(10, 50, 300, 20), "Controls: WASD Move, J/K Up/Down, Shift Fast");
        GUI.Label(new Rect(10, 70, 300, 20), "Right Click + Mouse to Look");
        GUI.Label(new Rect(10, 90, 300, 20), "Q: Exit Application | R: Refresh Connection");
    }
}
