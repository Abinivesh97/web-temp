import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import subprocess
import os
from datetime import datetime

# Import Google API libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    import gspread
except ImportError:
    print("CRITICAL ERROR: Libraries not found. Run: pip install google-api-python-client google-auth-oauthlib gspread")

# --- CONFIGURATION ---
DRIVE_PARENT_FOLDER_ID = '1bCZ82Llm6ahel1VkOZjgCXRW7xCgc-tO'
SHEET_ID = '1Pgkk9wQCGQZweZ0na6gnZzQRkac-Ir3rB5Ub1Wurgds'

# File paths
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'token.json'

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

# --- DARK THEME PALETTE ---
COLORS = {
    'bg': '#2b2b2b',        # Main Window Background (Dark Gray)
    'panel': '#363636',     # Sections Background (Lighter Gray)
    'fg': '#ffffff',        # Main Text Color (White)
    'accent': '#007acc',    # Primary Blue (Links/Info)
    'btn_script': '#2ea043',# Green for Running Scripts
    'btn_upload': '#a371f7',# Purple for Uploading
    'btn_cycle': '#d29922', # Yellow/Orange for New Cycle
    'btn_text': '#ffffff',  # Text on buttons
    'entry_bg': '#1e1e1e',  # Input field background
    'entry_fg': "#000000"   # Input field text
}

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")

class AutomationApp:
    def __init__(self, master):
        self.master = master
        master.title("Batch Script Automation")
        master.geometry("750x550")
        master.configure(bg=COLORS['bg'])

        self.selected_upload_folder = tk.StringVar(master)
        self.cycle_label_var = tk.StringVar()  # Display current cycle name
        self.current_cycle_path = None         # Store the shared folder path

        self.output_root = os.path.join(os.getcwd(), "Script_Outputs")
        os.makedirs(self.output_root, exist_ok=True)

        self.drive_service = None
        self.sheets_client = None

        # Check for required bat files on startup
        self.check_required_files()

        # Authenticate immediately on launch
        self.authenticate_google()

        # Initialize the first cycle folder
        self.start_new_cycle()

        # UI Layout
        self.create_script_section(master)
        
        # Divider Line
        tk.Frame(master, height=1, bg=COLORS['fg']).pack(fill=tk.X, padx=20, pady=15)
        
        self.create_upload_section(master)

    def check_required_files(self):
        """Checks if the required batch files exist."""
        required_files = ["bat1.bat", "bat2.bat"]
        missing = [f for f in required_files if not os.path.exists(f)]
        if missing:
            messagebox.showwarning("Missing Files",
                                   f"The following script files are missing:\n{', '.join(missing)}\n\nPlease create them in the same folder as this app.")

    def start_new_cycle(self):
        """Creates a folder with format: Day_MonthName_RandomString"""
        now = datetime.now()
        
        # Format: 02_December_153045 (Date_Month_TimeAsRandom)
        day_str = now.strftime('%d')
        month_str = now.strftime('%B')
        Year_str = now.year
        random_str = now.strftime('%H%M%S') # Using time as the random unique string
        
        folder_name = f"{day_str}_{month_str}_{Year_str}_{random_str}"

        # Set the global path for this cycle
        self.current_cycle_path = os.path.join(self.output_root, folder_name)
        os.makedirs(self.current_cycle_path, exist_ok=True)

        # Update GUI text
        self.cycle_label_var.set(f"Active Cycle: {folder_name}")

        # Auto-fill the upload path
        self.selected_upload_folder.set(self.current_cycle_path)

    def authenticate_google(self):
        """Handles the Browser Login Flow."""
        creds = None
        if os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            except Exception:
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            if not creds:
                if not os.path.exists(CLIENT_SECRET_FILE):
                    messagebox.showerror("Missing File", f"Could not find {CLIENT_SECRET_FILE}.")
                    return
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    messagebox.showerror("Login Failed", f"Error: {e}")
                    return

        try:
            self.drive_service = build('drive', 'v3', credentials=creds)
            self.sheets_client = gspread.authorize(creds)
            print("Connected to Google Services.")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    # --- SCRIPT RUNNER GUI ---
    def create_script_section(self, master):
        # Styled LabelFrame
        frame = tk.LabelFrame(master, text="  1. Run Scripts  ", font=FONT_BOLD,
                              bg=COLORS['bg'], fg=COLORS['accent'], 
                              bd=1, relief="solid", padx=15, pady=15)
        frame.pack(padx=20, pady=10, fill="x")

        # Cycle Info Section
        cycle_frame = tk.Frame(frame, bg=COLORS['bg'])
        cycle_frame.pack(fill="x", pady=(0, 15))

        tk.Label(cycle_frame, textvariable=self.cycle_label_var, 
                 font=("Segoe UI", 12, "bold"), bg=COLORS['bg'], fg=COLORS['fg']).pack(side=tk.LEFT)

        self.btn_cycle = tk.Button(cycle_frame, text="Start New Cycle", command=self.start_new_cycle, 
                                   bg=COLORS['btn_cycle'], fg='black', font=FONT_BOLD,
                                   relief="flat", activebackground="#b07d1b")
        self.btn_cycle.pack(side=tk.RIGHT)

        # Script Buttons Grid
        btn_frame = tk.Frame(frame, bg=COLORS['bg'])
        btn_frame.pack(fill="x")

        self.btn_run1 = tk.Button(btn_frame, text="Run Script 1 (Date)", 
                                  bg=COLORS['btn_script'], fg=COLORS['btn_text'], font=FONT_MAIN,
                                  relief="flat", activebackground="#268538", activeforeground="white",
                                  command=lambda: self.run_script_async("bat1.bat", "script1_output.txt"))
        self.btn_run1.pack(side=tk.LEFT, expand=True, fill='x', padx=(0, 10), ipady=5)

        self.btn_run2 = tk.Button(btn_frame, text="Run Script 2 (Temp)", 
                                  bg=COLORS['btn_script'], fg=COLORS['btn_text'], font=FONT_MAIN,
                                  relief="flat", activebackground="#268538", activeforeground="white",
                                  command=lambda: self.run_script_async("bat2.bat", "script2_temp_values.txt"))
        self.btn_run2.pack(side=tk.LEFT, expand=True, fill='x', padx=(10, 0), ipady=5)

    def run_script_async(self, script, output_name):
        if not self.current_cycle_path:
            self.start_new_cycle()
        
        out_file = os.path.join(self.current_cycle_path, output_name)
        
        self.btn_run1.config(state='disabled', bg=COLORS['panel'])
        self.btn_run2.config(state='disabled', bg=COLORS['panel'])

        thread = threading.Thread(target=self._run_script_worker, args=(script, out_file), daemon=True)
        thread.start()

    def _run_script_worker(self, script, out_file, timeout=None):
        try:
            proc = subprocess.Popen(['cmd', '/c', script, out_file],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True)
            try:
                stdout_text, stderr_text = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.terminate()
                stdout_text, stderr_text = "", "Timeout"
                self.master.after(0, lambda: messagebox.showerror("Error", "Script Timed Out"))
                return

            if proc.returncode != 0:
                self.master.after(0, lambda: messagebox.showerror("Error", f"Script Failed:\n{stderr_text}"))
            else:
                self.master.after(0, lambda: messagebox.showinfo("Success", f"Saved: {os.path.basename(out_file)}"))

        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.master.after(0, lambda: (
                self.btn_run1.config(state='normal', bg=COLORS['btn_script']), 
                self.btn_run2.config(state='normal', bg=COLORS['btn_script'])
            ))

    # --- UPLOAD GUI ---
    def create_upload_section(self, master):
        frame = tk.LabelFrame(master, text="  2. Cloud Upload  ", font=FONT_BOLD,
                              bg=COLORS['bg'], fg=COLORS['btn_upload'], 
                              bd=1, relief="solid", padx=15, pady=15)
        frame.pack(padx=20, pady=5, fill="x")

        tk.Label(frame, text="Target Folder:", bg=COLORS['bg'], fg=COLORS['fg'], font=FONT_MAIN).pack(pady=(0,5), anchor="w")
        
        # Styled Entry
        entry = tk.Entry(frame, textvariable=self.selected_upload_folder, state='readonly',
                         bg=COLORS['entry_bg'], fg=COLORS['entry_fg'], 
                         insertbackground='white', font=("Consolas", 10), relief="flat")
        entry.pack(fill='x', pady=5, ipady=3)

        btn_frame = tk.Frame(frame, bg=COLORS['bg'])
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Browse Folder", command=self.select_folder,
                  bg=COLORS['panel'], fg=COLORS['fg'], font=FONT_MAIN,
                  relief="flat", activebackground="#4a4a4a", activeforeground="white").pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Upload to Drive & Log", command=self.upload_process,
                  bg=COLORS['btn_upload'], fg='white', font=FONT_BOLD,
                  relief="flat", activebackground="#864dc4", activeforeground="white").pack(side=tk.LEFT, padx=5)

    def select_folder(self):
        path = filedialog.askdirectory(initialdir=self.output_root)
        if path:
            self.selected_upload_folder.set(path)

    def upload_process(self):
        path = self.selected_upload_folder.get()
        if not path or not os.path.exists(path):
            return messagebox.showerror("Error", "Invalid folder selected.")

        if not self.drive_service:
            return messagebox.showerror("Error", "Google Services not connected.")

        folder_name = os.path.basename(path)
        
        # Using a non-blocking info box is hard in standard tkinter, so we use a print or small wait cursor
        self.master.config(cursor="watch")
        self.master.update()

        try:
            # 1. Create Remote Folder
            meta = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [DRIVE_PARENT_FOLDER_ID]}
            remote_folder = self.drive_service.files().create(body=meta, fields='id, webViewLink').execute()
            folder_id = remote_folder.get('id')
            link = remote_folder.get('webViewLink')

            # 2. Upload Files
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if os.path.isfile(full_path):
                    file_meta = {'name': item, 'parents': [folder_id]}
                    media = MediaFileUpload(full_path)
                    self.drive_service.files().create(body=file_meta, media_body=media).execute()

            # 3. Log to Sheets
            sheet = self.sheets_client.open_by_key(SHEET_ID).sheet1
            sheet.append_row([folder_name, link])

            self.master.config(cursor="")
            messagebox.showinfo("Upload Complete", f"Successfully uploaded!\nLink copied to sheet.")

        except Exception as e:
            self.master.config(cursor="")
            messagebox.showerror("Upload Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    AutomationApp(root)
    root.mainloop()