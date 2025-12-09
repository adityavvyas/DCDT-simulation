# Data Center Digital Twin Simulation

This Unity project simulates a Data Center Digital Twin, featuring procedural room generation, interactive server racks, live data visualization via heatmaps, and external connectivity through WebSockets.

## Features

- **Procedural Environment**: Automatically generates a server room layout with customizable parameters using `RoomGenerator`.
- **Free Camera Navigation**: 
  - Fly through the scene with standard WASD controls.
  - Adjustable movement speed and mouse sensitivity.
  - "Invert Y" option for camera rotation.
- **Interactive Racks**: 
  - Click on server racks to view detailed information.
  - Visual feedback on selection.
- **Heatmap Visualization**: 
  - Toggleable heatmap overlay to visualize temperature or power data across the data center.
  - Managed by `HeatmapManager`.
- **Live Data Integration**: 
  - Connects to an external data source (e.g., Python backend) via `WebSocketConnector`.
  - Updates simulation status in real-time.
- **UI Dashboard**: Displays simulation metrics and controls via `SimulationUI`.

## Controls

### Camera Movement
| Key | Action |
| :--- | :--- |
| **W / A / S / D** | Move Forward / Left / Backward / Right |
| **J / K** | Move Up / Down |
| **Shift (Hold)** | Move Faster (Speed Multiplier) |
| **Right Click (Hold)** | Look around (Mouse) |

### Other Controls
| Key | Action |
| :--- | :--- |
| **Q** | Exit Application (or Stop Play Mode) |
| **F** | Toggle Fullscreen |
| **R** | Refresh Connection |

## Setup & Installation

1.  **Prerequisites**:
    - Unity 2021.3 or later (suggested based on common versions, check `ProjectSettings/ProjectVersion.txt` if specific version is needed).
    - Data source/backend server (if using live data features).

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/adityavvyas/DCDT-simulation.git
    ```

3.  **Open in Unity**:
    - Add the cloned folder to Unity Hub.
    - Open the project.

4.  **Run**:
    - Open the main scene (likely in `Assets/Scenes` or root `Assets`).
    - Press **Play**.

## Directory Structure

- `Assets/Scripts`: Core logic for camera, generation, UI, and networking.
- `Assets/Prefabs`: Reusable game objects (Racks, UI elements, etc.).
- `ProjectSettings`: Unity project configuration.

## Development

- **Scripts**: Written in C#.
- **Version Control**: Git initialized with Unity-specific `.gitignore`.
- **Sharing**: See [Sharing_Instructions.md](Sharing_Instructions.md) for how to send this project to others.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
```
