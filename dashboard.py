import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import config
import monitors
import privacy
import logger_setup

logger = logger_setup.get_logger()

class MonitoringDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("System Activity & Exam Monitor - Control Center")
        self.root.geometry("620x580")
        self.root.resizable(False, False)

        # Monitoring state
        self.is_monitoring = False
        self.stop_event = None
        self.threads = []

        # Ensure folders exist
        config.init_directories()

        self._build_ui()
        self._start_refresh_loop()

    def _build_ui(self):
        # 1. Header Frame
        header_frame = tk.Frame(self.root, bg="#2C3E50", pady=12)
        header_frame.pack(fill="x")

        title_label = tk.Label(
            header_frame,
            text="SYSTEM ACTIVITY & EXAM MONITOR",
            font=("Arial", 14, "bold"),
            fg="#ECF0F1",
            bg="#2C3E50"
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_frame,
            text="Authorized Local Telemetry & Proctoring Tool",
            font=("Arial", 9),
            fg="#BDC3C7",
            bg="#2C3E50"
        )
        subtitle_label.pack()

        # 2. Status Banner
        status_frame = tk.Frame(self.root, pady=10)
        status_frame.pack(fill="x")

        self.status_label = tk.Label(
            status_frame,
            text="STATUS: STOPPED",
            font=("Arial", 12, "bold"),
            fg="#E74C3C"
        )
        self.status_label.pack()

        # 3. Telemetry Metrics Cards Frame
        metrics_frame = tk.LabelFrame(self.root, text=" Real-Time Telemetry Counters ", font=("Arial", 10, "bold"), padx=15, pady=10)
        metrics_frame.pack(fill="x", padx=20, pady=5)

        # 4 Metric Labels
        self.lbl_screenshots = tk.Label(metrics_frame, text="Screenshots Captured: 0", font=("Arial", 10), anchor="w")
        self.lbl_screenshots.grid(row=0, column=0, sticky="w", pady=4, padx=10)

        self.lbl_keystrokes = tk.Label(metrics_frame, text="Keystrokes Logged: 0", font=("Arial", 10), anchor="w")
        self.lbl_keystrokes.grid(row=0, column=1, sticky="w", pady=4, padx=10)

        self.lbl_clipboard = tk.Label(metrics_frame, text="Clipboard Updates: 0", font=("Arial", 10), anchor="w")
        self.lbl_clipboard.grid(row=1, column=0, sticky="w", pady=4, padx=10)

        self.lbl_errors = tk.Label(metrics_frame, text="System Errors: 0", font=("Arial", 10), anchor="w")
        self.lbl_errors.grid(row=1, column=1, sticky="w", pady=4, padx=10)

        # 4. Control Buttons Frame
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack(fill="x", padx=20)

        self.btn_start = tk.Button(
            btn_frame,
            text="Start Monitoring",
            font=("Arial", 10, "bold"),
            bg="#27AE60",
            fg="white",
            padx=12,
            pady=5,
            command=self.start_monitoring
        )
        self.btn_start.grid(row=0, column=0, padx=6)

        self.btn_stop = tk.Button(
            btn_frame,
            text="Stop Monitoring",
            font=("Arial", 10, "bold"),
            bg="#C0392B",
            fg="white",
            padx=12,
            pady=5,
            state="disabled",
            command=self.stop_monitoring
        )
        self.btn_stop.grid(row=0, column=1, padx=6)

        self.btn_purge = tk.Button(
            btn_frame,
            text="Purge Test Data",
            font=("Arial", 10),
            bg="#7F8C8D",
            fg="white",
            padx=10,
            pady=5,
            command=self.purge_data
        )
        self.btn_purge.grid(row=0, column=2, padx=6)

        self.btn_open_folder = tk.Button(
            btn_frame,
            text="Open Output Folder",
            font=("Arial", 10),
            bg="#2980B9",
            fg="white",
            padx=10,
            pady=5,
            command=self.open_output_folder
        )
        self.btn_open_folder.grid(row=0, column=3, padx=6)

        # 5. Live Activity Log View
        log_frame = tk.LabelFrame(self.root, text=" Recent Application Activity ", font=("Arial", 10, "bold"), padx=10, pady=5)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.log_listbox = tk.Listbox(log_frame, font=("Consolas", 8), bg="#F8F9F9", selectbackground="#BDC3C7")
        scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.log_listbox.yview)
        self.log_listbox.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.log_listbox.pack(side="left", fill="both", expand=True)

    def _start_refresh_loop(self):
        """Refreshes telemetry counters and log file lines every 500ms."""
        self._update_telemetry()
        self.root.after(500, self._start_refresh_loop)

    def _update_telemetry(self):
        # Update metric labels from monitors.stats dictionary
        self.lbl_screenshots.config(text=f"Screenshots Captured: {monitors.stats['screenshots']}")
        self.lbl_keystrokes.config(text=f"Keystrokes Logged: {monitors.stats['keystrokes']}")
        self.lbl_clipboard.config(text=f"Clipboard Updates: {monitors.stats['clipboard']}")
        self.lbl_errors.config(text=f"System Errors: {monitors.stats['errors']}")

        # Read last 8 lines of system_monitor.log to show live log activity
        if os.path.exists(config.APP_LOG_FILE):
            try:
                with open(config.APP_LOG_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    last_lines = [line.strip() for line in lines[-12:]]

                    # Only update listbox if contents changed
                    current_items = list(self.log_listbox.get(0, tk.END))
                    if current_items != last_lines:
                        self.log_listbox.delete(0, tk.END)
                        for line in last_lines:
                            self.log_listbox.insert(tk.END, line)
                        self.log_listbox.yview_moveto(1.0)
            except Exception:
                pass

    def start_monitoring(self):
        if self.is_monitoring:
            return

        # Show Consent Dialog Box before starting
        consent = messagebox.askyesno(
            "Explicit User Consent Required",
            "This application will record system activity (screenshots, keystrokes, and clipboard) "
            "for testing and proctoring demonstration.\n\n"
            "All data is saved strictly locally on this device.\n\n"
            "Do you grant permission to start monitoring?"
        )

        if not consent:
            return

        self.is_monitoring = True
        self.stop_event = threading.Event()

        # Update button states
        self.status_label.config(text="STATUS: MONITORING ACTIVE", fg="#27AE60")
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.btn_purge.config(state="disabled")

        # Spawn monitoring threads
        self.threads = [
            threading.Thread(target=monitors.run_screenshot_monitor, args=(self.stop_event,), name="ScreenshotThread"),
            threading.Thread(target=monitors.run_clipboard_monitor,  args=(self.stop_event,), name="ClipboardThread"),
            threading.Thread(target=monitors.run_keyboard_monitor,   args=(self.stop_event,), name="KeyboardThread"),
        ]

        if config.ENABLE_AUDIO:
            self.threads.append(
                threading.Thread(target=monitors.run_audio_monitor, args=(self.stop_event,), name="AudioThread")
            )

        for t in self.threads:
            t.daemon = True
            t.start()

        logger.info("[Dashboard] User granted consent. All monitors started.")

    def stop_monitoring(self):
        if not self.is_monitoring:
            return

        self.status_label.config(text="STATUS: STOPPING...", fg="#E67E22")
        self.root.update_idletasks()

        # Signal background threads to stop
        if self.stop_event:
            self.stop_event.set()

        # Wait for threads to finish
        for t in self.threads:
            t.join(timeout=2)

        self.is_monitoring = False
        self.status_label.config(text="STATUS: STOPPED", fg="#E74C3C")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.btn_purge.config(state="normal")

        logger.info("[Dashboard] Monitoring stopped by user from dashboard.")
        messagebox.showinfo("Monitoring Stopped", "Monitoring stopped cleanly. All files saved.")

    def purge_data(self):
        if self.is_monitoring:
            messagebox.showwarning("Warning", "Please stop monitoring before purging data.")
            return

        confirm = messagebox.askyesno(
            "Confirm Data Purge",
            "Are you sure you want to delete all collected screenshots, logs, and clipboard data?"
        )
        if confirm:
            privacy.purge_collected_data()
            monitors.stats["screenshots"] = 0
            monitors.stats["keystrokes"] = 0
            monitors.stats["clipboard"] = 0
            monitors.stats["errors"] = 0
            self._update_telemetry()
            self.log_listbox.delete(0, tk.END)
            messagebox.showinfo("Success", "All collected test data has been deleted.")

    def open_output_folder(self):
        """Opens Windows Explorer directly to the output folder."""
        if os.path.exists(config.OUTPUT_DIR):
            os.startfile(config.OUTPUT_DIR)
        else:
            messagebox.showinfo("Notice", "Output folder does not exist yet.")

def main():
    root = tk.Tk()
    app = MonitoringDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
