import cv2
import pyautogui
import numpy as np
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import time
import os
import sys
import shutil
from datetime import datetime

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text: return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffff", relief='solid', borderwidth=1,
                         font=("Segoe UI", "8", "normal"), padx=5, pady=2)
        label.pack()

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw: tw.destroy()

class ScreenRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("TifaLAB")
        self.root.geometry("200x140")
        
        # Glassy White Theme
        self.bg_color = "#ffffff"
        self.root.configure(bg=self.bg_color)
        self.root.attributes("-alpha", 0.94)
        self.root.resizable(False, False)

        # Cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.cleanup_temps()

        # Set Favicon
        try:
            icon_path = resource_path("favicon.ico")
            if os.path.exists(icon_path):
                if sys.platform.startswith("win"):
                    self.root.iconbitmap(icon_path)
                else:
                    self.icon = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(False, self.icon)
        except Exception:
            pass

        self.recording = False
        self.paused = False
        self.cancelled = False
        self.start_time = 0
        self.pause_start_time = 0
        self.total_paused_duration = 0
        
        self.resolutions = {"360p": (640,360), "480p": (854,480), "720p": (1280,720), "1080p": (1920,1080)}
        self.modes = ["Screen", "Cam", "Both"]

        # Styles
        self.label_style = {"bg": self.bg_color, "fg": "#333333", "font": ("Segoe UI", 8, "bold")}
        self.btn_style = {"font": ("Segoe UI", 8, "bold"), "relief": "flat", "cursor": "hand2"}

        # --- Setup View ---
        self.setup_frame = tk.Frame(root, bg=self.bg_color)
        self.setup_frame.pack(fill="both", expand=True)
        
        self.setup_frame.grid_columnconfigure(0, weight=1)
        self.setup_frame.grid_columnconfigure(1, weight=1)
        self.setup_frame.grid_rowconfigure(0, weight=1)
        self.setup_frame.grid_rowconfigure(5, weight=1)

        tk.Label(self.setup_frame, text="TifaLAB Recorder", font=("Segoe UI", 10, "bold"), bg=self.bg_color, fg="#5c6bc0").grid(row=0, column=0, columnspan=2, pady=(10,2))

        tk.Label(self.setup_frame, text="Mode:", **self.label_style).grid(row=1, column=0, sticky="e", padx=5)
        self.mode_var = tk.StringVar(value="Screen")
        self.mode_menu = tk.OptionMenu(self.setup_frame, self.mode_var, *self.modes)
        self.mode_menu.config(bg="#f0f0f0", fg="#333333", highlightthickness=0, width=8, font=("Segoe UI", 7))
        self.mode_menu.grid(row=1, column=1, sticky="w", pady=1)

        tk.Label(self.setup_frame, text="Res:", **self.label_style).grid(row=2, column=0, sticky="e", padx=5)
        self.quality_var = tk.StringVar(value="720p")
        self.quality_menu = tk.OptionMenu(self.setup_frame, self.quality_var, *self.resolutions.keys())
        self.quality_menu.config(bg="#f0f0f0", fg="#333333", highlightthickness=0, width=8, font=("Segoe UI", 7))
        self.quality_menu.grid(row=2, column=1, sticky="w", pady=1)

        self.mouse_var = tk.BooleanVar(value=True)
        self.mouse_chk = tk.Checkbutton(self.setup_frame, text="Show Mouse", variable=self.mouse_var, 
                                        bg=self.bg_color, fg="#333333", selectcolor="#ffffff", font=("Segoe UI", 7))
        self.mouse_chk.grid(row=3, column=0, columnspan=2, pady=1)

        self.start_btn = tk.Button(self.setup_frame, text="START RECORDING", command=self.start_recording, 
                                   bg="#5c6bc0", fg="white", width=20, **self.btn_style)
        self.start_btn.grid(row=4, column=0, columnspan=2, pady=(5, 10))
        ToolTip(self.start_btn, "Begin Recording")

        # --- Recording View ---
        self.rec_frame = tk.Frame(root, bg=self.bg_color)
        
        self.rec_header = tk.Frame(self.rec_frame, bg=self.bg_color)
        self.rec_header.pack(fill="x", padx=10, pady=(5,0))
        
        tk.Label(self.rec_header, text="● REC", font=("Segoe UI", 8, "bold"), bg=self.bg_color, fg="#e91e63").pack(side="left")
        self.timer_label = tk.Label(self.rec_header, text="00:00:00", font=("Consolas", 12, "bold"), bg=self.bg_color, fg="#333333")
        self.timer_label.pack(side="right")

        self.rec_btns = tk.Frame(self.rec_frame, bg=self.bg_color)
        self.rec_btns.pack(pady=5)
        
        self.pause_btn = tk.Button(self.rec_btns, text="⏸", command=self.toggle_pause, bg="#4caf50", fg="white", width=4, font=("Segoe UI", 10))
        self.pause_btn.pack(side="left", padx=2)
        self.pause_tip = ToolTip(self.pause_btn, "Pause Recording")
        
        self.stop_btn = tk.Button(self.rec_btns, text="⏹", command=self.stop_recording, bg="#f44336", fg="white", width=4, font=("Segoe UI", 10))
        self.stop_btn.pack(side="left", padx=2)
        ToolTip(self.stop_btn, "Stop & Save")
        
        self.cancel_btn = tk.Button(self.rec_btns, text="✖", command=self.cancel_recording, bg="#9e9e9e", fg="white", width=4, font=("Segoe UI", 10))
        self.cancel_btn.pack(side="left", padx=2)
        ToolTip(self.cancel_btn, "Cancel & Discard")

    def cleanup_temps(self):
        # Remove leftover temp files
        for f in os.listdir("."):
            if f.startswith("temp_rec_") and f.endswith(".mp4"):
                try: os.remove(f)
                except: pass

    def on_closing(self):
        self.recording = False
        self.cleanup_temps()
        self.root.destroy()

    def switch_to_mini(self):
        self.setup_frame.pack_forget()
        self.root.geometry("200x75")
        self.rec_frame.pack(fill="both", expand=True)

    def switch_to_full(self):
        self.rec_frame.pack_forget()
        self.root.geometry("200x140")
        self.setup_frame.pack(fill="both", expand=True)

    def update_timer(self):
        if self.recording:
            if not self.paused:
                elapsed_time = int(time.time() - self.start_time - self.total_paused_duration)
                mins, secs = divmod(elapsed_time, 60)
                hours, mins = divmod(mins, 60)
                self.timer_label.config(text=f"{hours:02d}:{mins:02d}:{secs:02d}")
            self.root.after(1000, self.update_timer)

    def toggle_pause(self):
        if not self.paused:
            self.paused = True
            self.pause_start_time = time.time()
            self.pause_btn.config(text="▶", bg="#4caf50")
            self.pause_tip.text = "Resume Recording"
        else:
            self.paused = False
            self.total_paused_duration += time.time() - self.pause_start_time
            self.pause_btn.config(text="⏸", bg="#4caf50")
            self.pause_tip.text = "Pause Recording"

    def start_recording(self):
        self.recording = True
        self.paused = False
        self.cancelled = False
        self.start_time = time.time()
        self.total_paused_duration = 0
        self.switch_to_mini()
        self.update_timer()
        threading.Thread(target=self.record_loop, daemon=True).start()

    def stop_recording(self):
        if messagebox.askyesno("Stop", "Save recording?"):
            self.recording = False
            self.switch_to_full()

    def cancel_recording(self):
        if messagebox.askyesno("Cancel", "Discard recording?"):
            self.cancelled = True
            self.recording = False
            self.switch_to_full()
            self.timer_label.config(text="00:00:00")

    def record_loop(self):
        res_name = self.quality_var.get()
        target_res = self.resolutions[res_name]
        mode = self.mode_var.get()
        temp_name = f"temp_rec_{int(time.time())}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = 20.0
        out = cv2.VideoWriter(temp_name, fourcc, fps, target_res)
        cap = None
        if mode in ["Cam", "Both"]:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened(): cap = None

        try:
            while self.recording:
                if self.paused:
                    time.sleep(0.1)
                    continue
                loop_start = time.time()
                frame = None
                try:
                    if mode == "Screen":
                        img = pyautogui.screenshot()
                        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                        if self.mouse_var.get():
                            mx, my = pyautogui.position()
                            cv2.circle(frame, (mx, my), 8, (0, 0, 255), -1)
                    elif mode == "Cam":
                        if cap:
                            ret, frame = cap.read()
                            if not ret: frame = None
                    elif mode == "Both":
                        img = pyautogui.screenshot()
                        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                        if self.mouse_var.get():
                            mx, my = pyautogui.position()
                            cv2.circle(frame, (mx, my), 8, (0, 0, 255), -1)
                        if cap:
                            ret, cam_frame = cap.read()
                            if ret:
                                h, w, _ = frame.shape
                                cam_h = h // 4
                                cam_w = int(cam_frame.shape[1] * (cam_h / cam_frame.shape[0]))
                                cam_f = cv2.resize(cam_frame, (cam_w, cam_h))
                                m = 20
                                frame[h-cam_h-m:h-m, w-cam_w-m:w-m] = cam_f
                    if frame is not None:
                        out.write(cv2.resize(frame, target_res, interpolation=cv2.INTER_AREA))
                except Exception: pass
                wait = max(0, (1.0/fps) - (time.time() - loop_start))
                time.sleep(wait)
        finally:
            out.release()
            if cap: cap.release()
            time.sleep(0.3) # Give OS time to release file handle
            if not self.recording and not self.cancelled:
                self.root.after(0, lambda: self.save_file_workflow(temp_name))
            elif self.cancelled:
                if os.path.exists(temp_name):
                    try: os.remove(temp_name)
                    except: pass

    def save_file_workflow(self, temp_name):
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = filedialog.asksaveasfilename(defaultextension=".mp4", initialfile=f"Rec_{ts}.mp4", filetypes=[("MP4", "*.mp4")], title="Save")
        if file_path:
            # Try to rename with retries for PermissionError
            for _ in range(5):
                try:
                    if os.path.exists(file_path): os.remove(file_path)
                    shutil.move(temp_name, file_path)
                    messagebox.showinfo("Success", "Saved!")
                    return
                except (PermissionError, OSError) as e:
                    # On Windows, winerror 17 is "The system cannot move the file to a different disk drive"
                    # shutil.move should handle this, but if we still get errors, we retry a few times (except for cross-drive if it persists)
                    win_err = getattr(e, 'winerror', None)
                    if win_err == 17: 
                        # This shouldn't happen with shutil.move, but if it does, retrying won't help
                        break
                    
                    # For other errors like PermissionError (file busy), retry
                    time.sleep(0.5)
            messagebox.showerror("Error", f"Could not save file: {e}")
        else:
            # User cancelled, delete temp
            if os.path.exists(temp_name):
                try: os.remove(temp_name)
                except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenRecorder(root)
    root.mainloop()