using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;
using System.IO;

public class BuildScript
{
    [MenuItem("Build/Build and Run Windows Executable")]
    public static void BuildAndRunGame()
    {
        PerformBuild(true);
    }


    [MenuItem("Build/Build Only (Windows Executable)")]
    public static void BuildGame()
    {
        PerformBuild(BuildTarget.StandaloneWindows64, false);
    }

    [MenuItem("Build/Build Only (Linux Executable)")]
    public static void BuildGameLinux()
    {
        PerformBuild(BuildTarget.StandaloneLinux64, false);
    }

    [MenuItem("Build/Build Only (macOS Executable)")]
    public static void BuildGameMacOS()
    {
        PerformBuild(BuildTarget.StandaloneOSX, false);
    }

    private static void PerformBuild(bool autoRun)
    {
        PerformBuild(BuildTarget.StandaloneWindows64, autoRun);
    }

    private static void PerformBuild(BuildTarget target, bool autoRun)
    {
        // Check if the build target is supported/installed
        if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Standalone, target))
        {
            string moduleName = "unknown";
            if (target == BuildTarget.StandaloneLinux64) moduleName = "Linux Build Support (Mono/IL2CPP)";
            if (target == BuildTarget.StandaloneOSX) moduleName = "Mac Build Support (Mono/IL2CPP)";

            Debug.LogError($"Build Target '{target}' is not installed or supported on this Unity Editor instance.\nPlease open Unity Hub -> Installs -> Click 'Add modules' (gear icon) on this version -> Select '{moduleName}' -> Install.");
            return;
        }

        // Ensure Build directory exists
        string buildPath = "Builds";
        
        // Define extension and subfolder based on target
        string executableName = "DCDT_Simulation.exe";
        if (target == BuildTarget.StandaloneLinux64)
        {
            buildPath = Path.Combine(buildPath, "Linux");
            executableName = "DCDT_Simulation.x86_64";
        }
        else if (target == BuildTarget.StandaloneOSX)
        {
            buildPath = Path.Combine(buildPath, "MacOS");
            executableName = "DCDT_Simulation.app";
        }

        if (!Directory.Exists(buildPath))
        {
            Directory.CreateDirectory(buildPath);
        }

        // FORCE use of the current active scene to ensure what the user sees is what gets built
        string[] scenes = new string[] { UnityEngine.SceneManagement.SceneManager.GetActiveScene().path };
        
        Debug.Log($"Building Scene: {scenes[0]} for {target}");

        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
        buildPlayerOptions.scenes = scenes;
        buildPlayerOptions.locationPathName = Path.Combine(buildPath, executableName);
        buildPlayerOptions.target = target;
        
        // Set options
        buildPlayerOptions.options = BuildOptions.CompressWithLz4; // Optimize build size and load time
        if (autoRun) buildPlayerOptions.options |= BuildOptions.AutoRunPlayer;

        // Check and Switch Scripting Backend if needed
        ScriptingImplementation currentBackend = PlayerSettings.GetScriptingBackend(BuildTargetGroup.Standalone);
        
        // RULE: 
        // - Linux builds from Windows usually need IL2CPP (as you installed that).
        // - macOS builds from Windows CANNOT use IL2CPP (it's not supported). They MUST use Mono.
        
        bool needSwitch = false;
        ScriptingImplementation newBackend = currentBackend;
        string reason = "";

        if (target == BuildTarget.StandaloneLinux64 && currentBackend != ScriptingImplementation.IL2CPP)
        {
            needSwitch = true;
            newBackend = ScriptingImplementation.IL2CPP;
            reason = "Linux (IL2CPP)";
        }
        else if (target == BuildTarget.StandaloneOSX && currentBackend != ScriptingImplementation.Mono2x)
        {
            needSwitch = true;
            newBackend = ScriptingImplementation.Mono2x;
            reason = "macOS (Mono)";
        }

        if (needSwitch)
        {
            Debug.Log($"Switching Scripting Backend to {newBackend} for {target} compatibility...");
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Standalone, newBackend);
            
            EditorUtility.DisplayDialog("Configuration Updated", 
                $"The project has been configured for {reason}.\n(Note: macOS builds from Windows must use Mono).\n\nUnity is now recompiling scripts. Please wait for the spinner to finish, then CLICK THE BUILD MENU ITEM ONE MORE TIME.", 
                "OK");
            return;
        }

        Debug.Log($"Starting Build for {target} using {currentBackend} backend...");

        BuildReport report = BuildPipeline.BuildPlayer(buildPlayerOptions);
        BuildSummary summary = report.summary;

        if (summary.result == BuildResult.Succeeded)
        {
            Debug.Log("Build succeeded: " + summary.totalSize + " bytes");
            
            if (target == BuildTarget.StandaloneLinux64 || target == BuildTarget.StandaloneOSX)
            {
                string platformName = target == BuildTarget.StandaloneLinux64 ? "Linux" : "macOS";
                string fullBuildDir = Path.GetFullPath(buildPath);
                
                // --- CLEANUP to reduce size ---
                Debug.Log("Starting post-build cleanup...");
                
                // 1. Remove IL2CPP Backup folder (if exists)
                string backupDir = Path.Combine(fullBuildDir, $"{Path.GetFileNameWithoutExtension(executableName)}_BackUpThisFolder_ButDontShipItWithYourGame");
                if (Directory.Exists(backupDir)) DeleteDirectoryWithRetry(backupDir);

                // 2. Remove Burst Debug Info folder (often large and not needed)
                // Use wildcard search because the name prefix might vary (Project name vs Product name)
                string[] burstDirs = Directory.GetDirectories(fullBuildDir, "*_BurstDebugInformation_DoNotShip");
                foreach (string dir in burstDirs)
                {
                    DeleteDirectoryWithRetry(dir);
                }

                if (target == BuildTarget.StandaloneLinux64)
                {
                    // Create a helper shell script for easier launching on Linux
                    string shellScriptPath = Path.Combine(fullBuildDir, "run.sh");
                    string shellScriptContent = $"#!/bin/bash\n" +
                                                $"chmod +x \"./{executableName}\"\n" +
                                                $"./{executableName}";
                    File.WriteAllText(shellScriptPath, shellScriptContent);
                }

                // Open the build folder so the user can see the files
                EditorUtility.RevealInFinder(Path.Combine(fullBuildDir, executableName));
                
                string instructions = target == BuildTarget.StandaloneLinux64 
                    ? "1. Copy the ENTIRE 'Linux' folder.\n2. Send them the folder."
                    : "1. Copy the 'MacOS' folder.\n2. Compressing the '.app' file inside is recommended before sending to preserve permissions, but you can send the folder too.";

                EditorUtility.DisplayDialog("Build Successful", 
                    $"{platformName} build created successfully in:\n{fullBuildDir}\n\nTo share this with your friend:\n{instructions}\n\nInstructions are also in the README.", 
                    "OK");
            }
            else
            {
                // For Windows, standard behavior
                EditorUtility.RevealInFinder(buildPlayerOptions.locationPathName);
            }
        }

        if (summary.result == BuildResult.Failed)
        {
            Debug.Log("Build failed. Check the Console for details.");
        }
    }

    private static void DeleteDirectoryWithRetry(string path)
    {
        if (!Directory.Exists(path)) return;

        Debug.Log("Waiting for file handles to release...");
        System.Threading.Thread.Sleep(1000); // Short wait

        try
        {
            Debug.Log($"Deleting unnecessary folder to save space: {path}");
            Directory.Delete(path, true);
        }
        catch (System.Exception ex)
        {
            Debug.LogWarning($"Could not delete '{Path.GetFileName(path)}': {ex.Message}. You can delete it manually.");
        }
    }
}
