using UnityEngine;
using WebSocketSharp;
using System;
using System.Collections.Generic;

public class WebSocketConnector : MonoBehaviour
{
    public string serverUrl = "ws://localhost:8765";
    private WebSocket ws;
    private bool isConnected = false;

    // Thread-safe queue for dispatching to main thread
    private readonly Queue<Action> _executionQueue = new Queue<Action>();

    public event Action<SimulationState> OnSimulationStateReceived;

    void Start()
    {
        Connect();
    }

    public void Connect()
    {
        if (ws != null && ws.IsAlive) return;

        ws = new WebSocket(serverUrl);

        ws.OnOpen += (sender, e) =>
        {
            Enqueue(() => {
                isConnected = true;
                Debug.Log("WebSocket Connected to " + serverUrl);
            });
        };

        ws.OnMessage += (sender, e) =>
        {
            // Parse JSON in the background thread if possible, or just pass string
            try 
            {
                string json = e.Data;
                // Simple JSON parsing
                SimulationState state = JsonUtility.FromJson<SimulationState>(json);
                
                Enqueue(() => {
                    if (OnSimulationStateReceived != null)
                    {
                        OnSimulationStateReceived.Invoke(state);
                    }
                });
            }
            catch (Exception ex)
            {
                Debug.LogError("Error parsing WebSocket message: " + ex.Message);
            }
        };

        ws.OnClose += (sender, e) =>
        {
            Enqueue(() => {
                isConnected = false;
                Debug.LogWarning($"WebSocket Closed: {e.Reason}");
            });
        };

        ws.OnError += (sender, e) =>
        {
            Enqueue(() => Debug.LogError($"WebSocket Error: {e.Message}"));
        };

        ws.ConnectAsync();
    }

    public void Reconnect()
    {
        if (ws != null)
        {
            // Close asynchronously or just close
            ws.Close();
            ws = null;
        }
        isConnected = false;
        Debug.Log("Reconnecting to WebSocket server...");
        Connect();
    }

    void Update()
    {
        // Check for Reconnect Input (R key)
#if ENABLE_INPUT_SYSTEM
        if (UnityEngine.InputSystem.Keyboard.current != null && UnityEngine.InputSystem.Keyboard.current.rKey.wasPressedThisFrame)
        {
            Reconnect();
        }
#else
        if (Input.GetKeyDown(KeyCode.R))
        {
            Reconnect();
        }
#endif

        // Process the queue on the main thread
        lock (_executionQueue)
        {
            while (_executionQueue.Count > 0)
            {
                _executionQueue.Dequeue().Invoke();
            }
        }
    }

    private void Enqueue(Action action)
    {
        lock (_executionQueue)
        {
            _executionQueue.Enqueue(action);
        }
    }

    void OnDestroy()
    {
        if (ws != null)
        {
            ws.Close();
            ws = null;
        }
    }
}
