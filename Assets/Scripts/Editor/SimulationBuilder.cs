using UnityEngine;
using UnityEditor;
using System.IO;

public class SimulationBuilder
{
    [MenuItem("Simulation/Build Windows Exe")]
    public static void BuildGame()
    {
        // Get filename
        string path = "Builds";
        string appName = "DCDT_Simulation.exe";
        string fullPath = Path.Combine(path, appName);

        // Ensure build directory exists
        if (!Directory.Exists(path))
        {
            Directory.CreateDirectory(path);
        }

        // Get active scenes
        string[] levels = new string[] { UnityEngine.SceneManagement.SceneUtility.GetScenePathByBuildIndex(0) };
        if (levels[0] == "")
        {
            // If no scenes in build settings, use current open scene
            levels = new string[] { UnityEngine.SceneManagement.SceneManager.GetActiveScene().path };
        }

        // Build options
        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
        buildPlayerOptions.scenes = levels;
        buildPlayerOptions.locationPathName = fullPath;
        buildPlayerOptions.target = BuildTarget.StandaloneWindows64;
        buildPlayerOptions.options = BuildOptions.None;

        // Build
        UnityEditor.Build.Reporting.BuildReport report = BuildPipeline.BuildPlayer(buildPlayerOptions);
        UnityEditor.Build.Reporting.BuildSummary summary = report.summary;

        if (summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded)
        {
            Debug.Log("Build succeeded: " + summary.totalSize + " bytes");
            EditorUtility.RevealInFinder(fullPath);
        }

        if (summary.result == UnityEditor.Build.Reporting.BuildResult.Failed)
        {
            Debug.Log("Build failed");
        }
    }
}
