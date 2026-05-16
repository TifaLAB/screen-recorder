# TifaLAB Screen Recorder

This is a simple tool to record your computer screen and camera.
<img width="199" height="167" alt="image" src="https://github.com/user-attachments/assets/83805618-d908-4d65-a735-311f9a0af8a9" />
<br>

## What it can do:
*   Record **Screen**, **Camera**, or **Both** at the same time.
*   Choose video quality (like **1080p** or **720p**).
*   Window becomes small while recording so it stays out of the way.
*   Saves videos with the date and time so you don't lose them.

---

## 1. How to Setup (Do this first)

1.  Make sure you have **Python** installed.
2.  Open your command window in this folder and run:
    ```bash
    pip install -r requirements.txt
    ```

**Note for Linux users:**
Run this command to make recording work:
`sudo apt-get install scrot python3-tk python3-dev`

---

## 2. How to Use

To start the recorder, run:
```bash
python video-recorder.py
```

---

## 3. How to make a file to share (.exe or .app)

If you want to make a file that you can send to friends so they can run it without installing Python:

1.  Install the "Builder" tool:
    ```bash
    pip install pyinstaller
    ```

2.  Run the build script:
    ```bash
    python build_app.py
    ```

3.  After it finishes, look in the **`dist`** folder. Your file is there!

### ⚠️ Note for Windows Users:
When you run the `.exe` for the first time, Windows might show a blue box saying **"Windows protected your PC"**.
Don't worry! This is normal for apps you build yourself. 
To run it:
1.  Click **"More info"**.
2.  Click **"Run anyway"**.

---

## Files in this folder:
*   `video-recorder.py`: The main program.
*   `build_app.py`: The tool to make the shareable file.
*   `requirements.txt`: List of things the program needs to work.
*   `favicon.ico`: The program icon.
