import os
import sys
import subprocess

def build():
    # Dependencies
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # PyInstaller command
    # On Windows, data separator is ';', on Mac/Linux it is ':'
    separator = ";" if sys.platform.startswith("win") else ":"
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        f"--add-data=favicon.ico{separator}.",
        "video-recorder.py",
        "--name=TifaLAB_Recorder"
    ]

    # Add icon if it exists
    if os.path.exists("favicon.ico"):
        cmd.append(f"--icon=favicon.ico")
    
    # Mac specific: Create a .app bundle
    if sys.platform == "darwin":
        cmd.append("--windowed")
        # You can add more Mac-specific options here if needed

    print(f"Building for {sys.platform}...")
    subprocess.run(cmd)
    print("\nBuild complete! Check the 'dist' folder for your executable.")

if __name__ == "__main__":
    build()
