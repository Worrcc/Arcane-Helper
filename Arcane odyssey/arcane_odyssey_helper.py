import customtkinter as ctk
from PIL import Image
import os
import threading
import time
import pyautogui
import shutil
import json
import keyboard
import psutil
from tkinter import filedialog

# Set the theme and color appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class DashboardCard(ctk.CTkFrame):
    """A card for the tracked item."""
    def __init__(self, master, title, subtitle, status="Active", icon_text="📦", on_delete=None, on_toggle=None, enabled=True, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        # Card styling
        self.configure(fg_color="#1f2940", corner_radius=15, border_width=1, border_color="#2b3b55")

        # Top Bar (Delete Button)
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        
        if on_delete:
            self.del_btn = ctk.CTkButton(self.top_bar, text="✕", width=25, height=25,
                                       fg_color="transparent", hover_color="#ff4757",
                                       text_color="#a0aec0", font=("Arial", 12),
                                       command=on_delete)
            self.del_btn.pack(side="right")

        # Icon placeholder
        self.icon_label = ctk.CTkLabel(self, text=icon_text, font=("Arial", 30))
        self.icon_label.grid(row=1, column=0, pady=(0, 10), padx=10)

        # Title
        self.title_label = ctk.CTkLabel(self, text=title, font=("Roboto Medium", 14), text_color="#ffffff")
        self.title_label.grid(row=2, column=0, pady=(0, 5), padx=10)

        # Status/Subtitle
        self.status_color_active = "#4cc9f0"
        self.status_color_inactive = "#6c757d"
        self.status_color_alert = "#ff4757"
        
        self.status_label = ctk.CTkLabel(self, text=status, font=("Roboto", 11), text_color=self.status_color_active)
        self.status_label.grid(row=3, column=0, pady=(0, 10), padx=10)

        # Toggle Switch
        if on_toggle:
            self.switch_var = ctk.StringVar(value="on" if enabled else "off")
            self.switch = ctk.CTkSwitch(self, text="Search", command=on_toggle, 
                                      variable=self.switch_var, onvalue="on", offvalue="off",
                                      progress_color="#3d5afe")
            self.switch.grid(row=4, column=0, pady=(0, 20), padx=10)
            if enabled:
                self.switch.select()
            else:
                self.switch.deselect()

    def set_status(self, text, state="normal"):
        self.status_label.configure(text=text)
        if state == "alert":
            self.status_label.configure(text_color=self.status_color_alert)
        elif state == "active":
             self.status_label.configure(text_color=self.status_color_active)
        else:
             self.status_label.configure(text_color=self.status_color_inactive)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Arcane Odyssey Helper")
        self.geometry("900x750") 
        
        # Configure grid layout (Sidebar, Main Content)
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # --- COLORS ---
        self.bg_color = "#141b2d"
        self.sidebar_color = "#1f2940"
        self.accent_color = "#3d5afe" 
        self.text_color = "#ffffff"
        
        self.configure(fg_color=self.bg_color)

        # ================== LEFT SIDEBAR ==================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=self.sidebar_color)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(3, weight=1) 

        # App Logo/Title
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Arcane Helper", font=("Roboto Medium", 20, "bold"), text_color=self.text_color)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10), sticky="w")
        
        # Navigation Buttons
        self.nav_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="Item Notifier", 
            fg_color=self.accent_color, 
            text_color="#ffffff",
            hover_color="#2d3748", 
            anchor="w", 
            width=160, 
            height=40,
            corner_radius=8,
            font=("Roboto", 14)
        )
        self.nav_btn.grid(row=1, column=0, padx=20, pady=20)
        
        # Add Item Button
        self.add_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="+ Add Item", 
            fg_color="transparent", 
            border_width=1,
            border_color=self.accent_color,
            text_color="#ffffff",
            hover_color="#2d3748", 
            anchor="center", 
            width=160, 
            height=35,
            corner_radius=8,
            font=("Roboto", 12),
            command=self.add_new_item
        )
        self.add_btn.grid(row=2, column=0, padx=20, pady=10)

        # ================== MAIN CONTENT ==================
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1) # Make cards grid expand
        self.main_frame.grid_rowconfigure(4, weight=1) # Console expand

        # Header
        self.header_label = ctk.CTkLabel(self.main_frame, text="Item Notifier Dashboard", font=("Roboto Medium", 24), text_color=self.text_color, anchor="w")
        self.header_label.grid(row=0, column=0, pady=(10, 30), sticky="w")

        # Featured Status Panel
        self.status_panel = ctk.CTkFrame(self.main_frame, fg_color="#1f2940", corner_radius=15, height=100)
        self.status_panel.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        self.status_panel.grid_propagate(False)
        
        self.status_title = ctk.CTkLabel(self.status_panel, text="System Status", font=("Roboto Medium", 16), text_color="#4cc9f0")
        self.status_title.place(x=20, y=15)
        
        self.detection_status = ctk.CTkLabel(self.status_panel, text="Initializing...", font=("Roboto", 14), text_color="#a0aec0")
        self.detection_status.place(x=20, y=45)

        # Cards Grid
        self.cards_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.cards_frame.grid(row=2, column=0, sticky="nsew")
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)
        self.cards_frame.grid_columnconfigure(2, weight=1)

        # Console Section
        self.console_label = ctk.CTkLabel(self.main_frame, text="Console Log", font=("Roboto Medium", 14), text_color="#a0aec0", anchor="w")
        self.console_label.grid(row=3, column=0, sticky="w", pady=(20, 5))

        self.console_box = ctk.CTkTextbox(self.main_frame, height=150, corner_radius=10, fg_color="#0f1623", text_color="#a0aec0")
        self.console_box.grid(row=4, column=0, sticky="nsew")
        self.console_box.configure(state="disabled")

        # Data structure for items
        self.items = [] # List of dictionaries
        self.save_file = "items.json"

        # Ensure images folder exists
        if not os.path.exists("images"):
            os.makedirs("images")
            
        # Load items
        self.load_items()

        # State for scanning
        self.running = True
        
        # Start scanning thread
        self.scanner_thread = threading.Thread(target=self.scan_screen, daemon=True)
        self.scanner_thread.start()

        # Start Hotkey Listener
        try:
            keyboard.add_hotkey('ctrl+f', self.log_mouse_pos)
        except Exception as e:
            self.log_to_console(f"Error binding hotkey: {e}")

    def log_to_console(self, message):
        """Appends message to the console textbox."""
        # Use after to be thread-safe
        self.after(0, lambda: self._update_console(message))

    def _update_console(self, message):
        timestamp = time.strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}\n"
        
        self.console_box.configure(state="normal")
        self.console_box.insert("end", full_msg)
        self.console_box.see("end") # Auto scroll
        self.console_box.configure(state="disabled")

    def log_mouse_pos(self):
        x, y = pyautogui.position()
        self.log_to_console(f"Mouse Position: ({x}, {y})")

    def load_items(self):
        """Loads items from JSON file."""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r") as f:
                    data = json.load(f)
                    for item_data in data:
                        self.add_item_to_list(
                            item_data["name"], 
                            item_data["image"], 
                            enabled=item_data.get("enabled", True),
                            save=False # Don't re-save while loading
                        )
            except Exception as e:
                self.log_to_console(f"Error loading items: {e}")
        
        # If no items loaded, add default
        if not self.items:
             self.add_item_to_list("Atlantean Essence", "Atlantean.png", "🔮", save=True)

    def save_items(self):
        """Saves current items to JSON file."""
        data = []
        for item in self.items:
            data.append({
                "name": item["name"],
                "image": item["image"],
                "enabled": item["enabled"]
            })
        
        try:
            with open(self.save_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.log_to_console(f"Error saving items: {e}")

    def add_item_to_list(self, name, image_filename, icon="📦", enabled=True, save=True):
        """Creates a card and adds item to tracking list."""
        
        # Helper to toggle state
        def toggle_callback():
            # Find item in list
            for itm in self.items:
                if itm["name"] == name:
                    itm["enabled"] = not itm["enabled"]
                    status = "Active" if itm["enabled"] else "Disabled"
                    itm["card"].set_status(status, "active" if itm["enabled"] else "inactive")
                    self.log_to_console(f"Item '{name}' toggled: {status}")
                    self.save_items()
                    break

        # Helper to delete item
        def delete_callback():
            # Remove from list
            for i, itm in enumerate(self.items):
                if itm["name"] == name:
                    itm["card"].destroy() # Remove UI
                    self.items.pop(i)
                    self.rearrange_cards() # Fix grid
                    self.save_items()
                    self.log_to_console(f"Item '{name}' deleted.")
                    break

        card = DashboardCard(
            self.cards_frame, 
            name, 
            "Active" if enabled else "Disabled", 
            status="Active" if enabled else "Disabled", 
            icon_text=icon,
            on_toggle=toggle_callback,
            on_delete=delete_callback,
            enabled=enabled
        )
        
        self.items.append({
            "name": name,
            "image": image_filename,
            "card": card,
            "last_alert": 0,
            "enabled": enabled
        })
        
        if save:
            self.rearrange_cards() # Places the new card
            self.save_items()
            self.log_to_console(f"Added new item: {name}")
        else:
             # Just place it if loading (rearrange called manually or implicitly by loop)
             self.place_card(card, len(self.items)-1)

    def place_card(self, card, index):
        row = index // 3
        col = index % 3
        card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

    def rearrange_cards(self):
        """Re-grids all cards to fill gaps."""
        for i, item in enumerate(self.items):
            self.place_card(item["card"], i)

    def add_new_item(self):
        """Callback for the 'Add Item' button."""
        # 1. Ask for Item Name
        dialog = ctk.CTkInputDialog(text="Enter Item Name:", title="Add New Item")
        name = dialog.get_input()
        
        if not name:
            return 
            
        # 2. Ask for Image File
        file_path = filedialog.askopenfilename(
            title="Select Image for Item",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
        )
        
        if not file_path:
            return 

        # 3. Copy image to images folder
        filename = os.path.basename(file_path)
        dest_path = os.path.join("images", filename)
        
        try:
            shutil.copy(file_path, dest_path)
        except shutil.SameFileError:
            pass 
            
        # 4. Add to list
        self.add_item_to_list(name, filename)

    def scan_screen(self):
        """Background thread to look for the images."""
        
        # Initial delay to let UI load
        time.sleep(1)
        self.log_to_console("Scanner started.")
        
        while self.running:
            something_found = False
            active_scans = 0
            
            for item in self.items:
                # Skip if disabled
                if not item["enabled"]:
                    continue
                    
                active_scans += 1
                image_path = os.path.join("images", item["image"])
                
                if not os.path.exists(image_path):
                    item["card"].set_status("Missing Image", "inactive")
                    continue

                try:
                    item["card"].set_status("Scanning...", "active")
                    
                    # Search for the image on screen
                    # grayscale=False ensures color is checked, preventing misidentification of similarly shaped items
                    location = pyautogui.locateOnScreen(image_path, confidence=0.85, grayscale=False)
                    
                    if location:
                        something_found = True
                        item["card"].set_status("DETECTED!", "alert")
                        
                        current_time = time.time()
                        
                        if current_time - item["last_alert"] > 5:
                            item["last_alert"] = current_time
                            self.show_popup(item["name"])
                            self.log_to_console(f"FOUND: {item['name']} at {location}")
                    else:
                         item["card"].set_status("Scanning...", "active")
                            
                except Exception as e:
                     item["card"].set_status("Error", "inactive")
            
            # Update general status
            if something_found:
                self.update_status("Item Detected!", error=False)
            elif active_scans == 0:
                 self.update_status("No active trackers.", error=False)
            else:
                self.update_status("Scanning...", error=False)
            
            time.sleep(1) # Check every second

    def update_status(self, text, error=False):
        color = "#ff4757" if error else "#a0aec0"
        try:
            self.detection_status.configure(text=text, text_color=color)
        except:
            pass

    def show_popup(self, item_name):
        """Shows a custom popup window."""
        self.after(0, lambda: self._create_popup_window(item_name))

    def _create_popup_window(self, item_name):
        """Creates a non-intrusive notification-style popup in the bottom right."""
        popup = ctk.CTkToplevel(self)
        popup.title("ALERT")
        
        width = 350
        height = 100
        
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        
        x = screen_width - width - 20
        y = screen_height - height - 60 
        
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.attributes("-topmost", True) 
        popup.overrideredirect(True) 
        
        frame = ctk.CTkFrame(popup, fg_color="#1f2940", border_width=2, border_color="#3d5afe", corner_radius=10)
        frame.pack(expand=True, fill="both")

        label = ctk.CTkLabel(frame, text=f"{item_name} Detected!", font=("Roboto Medium", 16), text_color="#ffffff")
        label.pack(side="left", padx=20)
        
        close_btn = ctk.CTkButton(frame, text="✕", width=30, height=30, 
                                fg_color="transparent", hover_color="#ff4757", 
                                command=popup.destroy)
        close_btn.pack(side="right", padx=10)

        popup.after(5000, popup.destroy)

    def on_closing(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    # Single Instance Logic
    pid_file = "app.pid"
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                old_pid = int(f.read().strip())
            
            if psutil.pid_exists(old_pid):
                process = psutil.Process(old_pid)
                process.terminate()
                try:
                    process.wait(timeout=2)
                except psutil.TimeoutExpired:
                    process.kill()
        except Exception as e:
            print(f"Error checking/killing old instance: {e}")

    # Write current PID
    try:
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"Error writing PID: {e}")

    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
