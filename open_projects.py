import os
import paramiko
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import argparse
import re
import threading
import json
from pathlib import Path

# Add these global variables at the top level, after imports
workspace_vars = {}  # Store workspace variables
checkbuttons = {}  # Store checkbuttons
tree = None  # Will store the treeview
host_var = None  # Will store the host variable
log_text = None  # Will store the log text widget
log_message = None  # Will store the log message function
root = None  # Will store the main window
vsb = None  # Will store vertical scrollbar

def scan_remote_workspaces(host, user, base_path):
    """Scans the remote base path for VSCode workspace files using SSH."""
    try:
        user_base_path = base_path.replace("user", user)
        # Use system SSH to execute the find command, with proper Windows path handling
        if os.name == 'nt':  # Windows
            cmd = f'ssh -o ConnectTimeout=2 {host} "find {user_base_path} -type f -name \'*.code-workspace\' 2>/dev/null"'
        else:
            cmd = f"ssh -o ConnectTimeout=2 {host} find {user_base_path} -type f -name '*.code-workspace' 2>/dev/null"
            
        # Create a clean environment without SSH_AUTH_SOCK
        env = os.environ.copy()
        if 'SSH_AUTH_SOCK' in env:
            del env['SSH_AUTH_SOCK']
            
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            env=env,
            timeout=3  # Total timeout including the SSH timeout
        )
        
        # Don't treat permission denied as an error if we got some results
        workspaces = result.stdout.splitlines()
        if workspaces:
            return workspaces
            
        if result.returncode != 0:
            raise Exception(f"SSH command failed: {result.stderr}")
            
        return workspaces
        
    except subprocess.TimeoutExpired:
        error_message = f"Connection to {host} timed out after 2 seconds"
        print(error_message)
        return []
    except Exception as e:
        error_message = f"Failed to scan remote workspaces: {str(e)}\nType: {type(e)}"
        print(error_message)
        return []

def open_workspaces(selected_workspaces, host):
    """Opens the selected workspaces in VSCode with Remote SSH."""
    try:
        for workspace in selected_workspaces:
            # Ensure the path starts with /home/user
            if not workspace.startswith('/home/'):
                workspace = f"/home/{workspace}"
            
            # Use the same format as the PowerShell script
            print(f"Opening: code --remote ssh-remote+{host} {workspace}")  # Debug print
            subprocess.Popen([
                "code",
                "--remote",
                f"ssh-remote+{host}",
                workspace
            ], shell=True)  # Added shell=True for Windows compatibility
            
        messagebox.showinfo("Success", "Selected workspaces are being opened in VSCode.")
    except Exception as e:
        print(f"Error details: {str(e)}")  # Debug print
        messagebox.showerror("Error", f"Failed to open workspaces: {e}")

def parse_ssh_config():
    """Parse SSH config file and return list of hosts with their details."""
    hosts = []
    try:
        with open(os.path.expanduser('~/.ssh/config')) as f:
            current_host = None
            for line in f:
                line = line.strip()
                if line.startswith('Host '):
                    if current_host and 'hostname' in current_host and 'user' in current_host:
                        hosts.append(current_host)
                    current_host = {'name': line.split()[1]}
                elif current_host and line:
                    key, value = re.split(r'\s+', line, maxsplit=1)
                    key = key.lower()
                    if key == 'hostname':
                        current_host['hostname'] = value
                    elif key == 'user':
                        current_host['user'] = value
            
            # Add the last host if it exists
            if current_host and 'hostname' in current_host and 'user' in current_host:
                hosts.append(current_host)
    except Exception as e:
        print(f"Error parsing SSH config: {e}")
    return hosts

def get_settings_path():
    """Returns the path to the settings file."""
    return Path.home() / '.vscode_workspace_opener_settings.json'

def save_settings(host_name, selected_workspaces):
    """Saves the host and its selected workspaces to settings file."""
    try:
        settings_path = get_settings_path()
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
        else:
            settings = {}
        
        settings['last_host'] = host_name
        if 'workspace_selections' not in settings:
            settings['workspace_selections'] = {}
        settings['workspace_selections'][host_name] = selected_workspaces
        
        with open(settings_path, 'w') as f:
            json.dump(settings, f)
    except Exception as e:
        print(f"Failed to save settings: {e}")

def load_settings():
    """Loads settings from file."""
    try:
        settings_path = get_settings_path()
        if settings_path.exists():
            with open(settings_path) as f:
                return json.load(f)
    except Exception as e:
        print(f"Failed to load settings: {e}")
    return {'last_host': None, 'workspace_selections': {}}

def update_workspace_list(workspaces):
    global log_message
    if not workspaces:
        log_message(f"No workspaces found on {host}")
        return
    
    workspace_vars.clear()  # Clear existing workspace vars
    
    # Load previously selected workspaces for this host
    settings = load_settings()
    selected_workspaces = settings.get('workspace_selections', {}).get(host_var.get(), [])
    
    # Configure tag for alternating rows
    tree.tag_configure('oddrow', background='#f0f0f0')
    
    # Add new items
    for workspace in workspaces:
        # Use full path as unique identifier
        item_id = tree.insert('', 'end', 
                            values=('', os.path.splitext(os.path.basename(workspace))[0], workspace))
        # Set checkbox state based on exact path match
        var = tk.BooleanVar(value=workspace in selected_workspaces)
        
        # Create a specific callback for this workspace
        def make_callback(path):
            def callback(*args):
                selected = [w for w, v in workspace_vars.values() if v.get()]
                save_settings(host_var.get(), selected)
            return callback
            
        var.trace_add('write', make_callback(workspace))
        workspace_vars[item_id] = (workspace, var)
    
    refresh_workspace_list()

def populate_workspaces(host_data):
    global root, log_message
    workspace_vars.clear()
    # Clear existing items and checkbuttons
    for check in checkbuttons.values():
        check.destroy()
    checkbuttons.clear()
    tree.delete(*tree.get_children())
    
    host = host_data['hostname']
    user = host_data['user']
    base_path = "/home/user/git"
    
    log_message(f"Scanning workspaces on {host}...")
    
    def scan_thread():
        workspaces = scan_remote_workspaces(host, user, base_path)
        root.after(0, lambda: update_workspace_list(workspaces))
    
    # Start scanning in a separate thread
    threading.Thread(target=scan_thread, daemon=True).start()

def refresh_workspace_list():
    global vsb
    # Clear existing items and checkbuttons
    for check in checkbuttons.values():
        check.destroy()
    checkbuttons.clear()
    tree.delete(*tree.get_children())
    
    # Configure tag for alternating rows
    tree.tag_configure('oddrow', background='#f0f0f0')
    
    # Add workspace items
    for item_id, (workspace, var) in workspace_vars.items():
        base_name = os.path.splitext(os.path.basename(workspace))[0]
        
        # Insert item with checkbox placeholder
        tree.insert('', 'end', item_id, 
                   values=('', base_name, workspace),
                   tags=('oddrow',) if len(tree.get_children()) % 2 else ())
        
        # Create and place checkbutton with proper styling
        check = ttk.Checkbutton(tree, 
                              variable=var, 
                              style='Workspace.TCheckbutton',
                              padding=(0, 0, 0, 0))
        checkbuttons[item_id] = check

    # Update all checkbox positions after all items are inserted
    root.update_idletasks()
    position_all_checkboxes()

def position_all_checkboxes():
    """Position all checkboxes correctly"""
    for item_id, check in checkbuttons.items():
        bbox = tree.bbox(item_id, 'select')
        if bbox:
            # Position in the center of the cell, with a fixed offset from left
            x = bbox[0] + 15  # Fixed left offset
            y = bbox[1] + bbox[3]//2
            check.place(x=x, y=y, anchor='w')
        else:
            check.place_forget()

def main():
    global workspace_vars, checkbuttons, tree, host_var, log_text, log_message, root, vsb
    
    root = tk.Tk()
    root.title("Open Remote Workspaces in VSCode")
    root.geometry("1400x800")  # Larger default window size
    
    # Configure style
    style = ttk.Style()
    style.configure('Modern.TButton', 
                   padding=10, 
                   font=('Segoe UI', 10))
    style.configure('Header.TLabel', 
                   font=('Segoe UI', 10, 'bold'),
                   padding=5)
    style.configure('Column.TLabel',
                   font=('Segoe UI', 10),
                   padding=5)
    
    # Create main container with two panels
    main_container = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Left panel for host selection and workspaces (70% of width)
    left_panel = ttk.Frame(main_container)
    main_container.add(left_panel, weight=7)
    
    # Right panel for log (30% of width)
    right_panel = ttk.LabelFrame(main_container, text="Log")
    main_container.add(right_panel, weight=3)
    
    # Log text area in right panel (smaller height)
    log_text = tk.Text(right_panel, wrap=tk.WORD, font=('Consolas', 9), height=8)
    log_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
    
    # Add scrollbar to log
    log_scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=log_text.yview)
    log_scrollbar.pack(side="right", fill="y")
    log_text.configure(yscrollcommand=log_scrollbar.set)
    
    def log_message(message):
        log_text.insert(tk.END, f"{message}\n")
        log_text.see(tk.END)
    
    # Host selection frame at top of left panel (minimal height)
    host_frame = ttk.LabelFrame(left_panel, text="Remote Host")
    host_frame.pack(padx=5, pady=(5,2), fill="x")
    
    # Get hosts from SSH config
    hosts = parse_ssh_config()
    if not hosts:
        log_message("No hosts found in SSH config file.")
        return

    # Workspace list frame (takes most of the space)
    workspace_list_frame = ttk.LabelFrame(left_panel, text="Workspaces")
    workspace_list_frame.pack(padx=5, pady=(2,5), fill="both", expand=True)
    
    # Create Treeview with larger height
    columns = ('select', 'name', 'path')
    tree = ttk.Treeview(workspace_list_frame, 
                        columns=columns, 
                        show='headings', 
                        selectmode='none',
                        height=25)
    
    # Define column headings
    tree.heading('select', text='')
    tree.heading('name', text='Project Name', command=lambda: sort_treeview('name'))
    tree.heading('path', text='Full Path', command=lambda: sort_treeview('path'))
    
    # After creating the tree and before the scrollbars, add this style configuration
    style.configure("Workspace.TCheckbutton", 
                   background="white",
                   padding=0,
                   relief='flat',
                   borderwidth=0)
    
    # Configure column properties with better proportions
    tree.column('select', width=30, stretch=False, anchor='center')
    tree.column('name', width=300, stretch=True, anchor='w', minwidth=200)
    tree.column('path', width=600, stretch=True, anchor='w', minwidth=400)
    
    # Add select all button above the tree
    select_frame = ttk.Frame(workspace_list_frame)
    select_frame.grid(row=0, column=0, sticky='nw', padx=5, pady=2)
    
    def toggle_all():
        select_all = not any(var.get() for _, var in workspace_vars.values())
        for _, var in workspace_vars.values():
            var.set(select_all)
    
    select_all_btn = ttk.Button(select_frame, 
                               text="Select All",
                               style='Modern.TButton',
                               command=toggle_all)
    select_all_btn.pack(side='left')
    
    # Add scrollbars
    vsb = ttk.Scrollbar(workspace_list_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(workspace_list_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    
    # Grid layout for table and scrollbars
    tree.grid(row=1, column=0, sticky='nsew')
    vsb.grid(row=1, column=1, sticky='ns')
    hsb.grid(row=2, column=0, sticky='ew')
    
    # Configure grid weights
    workspace_list_frame.grid_columnconfigure(0, weight=1)
    workspace_list_frame.grid_rowconfigure(0, weight=1)
    
    workspace_vars = {}  # Initialize empty dictionary
    checkbuttons = {}  # Initialize empty dictionary
    
    def sort_treeview(column):
        items = [(tree.set(item, column), item) for item in tree.get_children('')]
        items.sort(reverse=getattr(sort_treeview, 'reverse', False))
        
        # Rearrange items in sorted positions
        for index, (val, item) in enumerate(items):
            tree.move(item, '', index)
        
        # Switch sort order for next time
        sort_treeview.reverse = not getattr(sort_treeview, 'reverse', False)
        
        # Update column headings to show sort state
        for col in ('name', 'path'):
            if col == column:
                direction = " ↓" if sort_treeview.reverse else " ↑"
            else:
                direction = ""
            tree.heading(col, text=f"{'Project Name' if col == 'name' else 'Full Path'}{direction}")
    
    # Host selection dropdown with modern styling
    host_var = tk.StringVar()
    host_names = [host['name'] for host in hosts]
    host_dropdown = ttk.Combobox(host_frame, 
                                textvariable=host_var, 
                                values=host_names, 
                                state="readonly",
                                font=('Segoe UI', 10))
    host_dropdown.pack(padx=5, pady=5, fill="x")
    
    def on_host_select(event=None):
        selected_host = host_var.get()
        # Don't clear selections when switching hosts
        host_data = next((host for host in hosts if host['name'] == selected_host), None)
        if host_data:
            populate_workspaces(host_data)
    
    host_dropdown.bind('<<ComboboxSelected>>', on_host_select)
    
    # Set last used host if available
    last_host = load_settings().get('last_host')
    if last_host and last_host in host_names:
        host_dropdown.set(last_host)
        root.after(100, on_host_select)  # Load workspaces after GUI is ready

    # Bottom button frame
    button_frame = ttk.Frame(left_panel)
    button_frame.pack(pady=10, fill="x")
    
    def open_workspaces_with_log(selected_workspaces, host):
        """Opens the selected workspaces in VSCode with Remote SSH."""
        try:
            for workspace in selected_workspaces:
                if not workspace.startswith('/home/'):
                    workspace = f"/home/{workspace}"
                
                log_message(f"Opening: code --remote ssh-remote+{host} {workspace}")
                subprocess.Popen([
                    "code",
                    "--remote",
                    f"ssh-remote+{host}",
                    workspace
                ], shell=True)
                
            log_message("Selected workspaces are being opened in VSCode.")
        except Exception as e:
            log_message(f"Error details: {str(e)}")

    def on_open():
        if not workspace_vars:
            log_message("Please select a host first.")
            return
            
        # Get selected workspaces by full path
        selected = [workspace for workspace, var in workspace_vars.values() if var.get()]
        if not selected:
            log_message("Please select at least one workspace.")
            return
            
        selected_host = host_var.get()
        host_data = next((host for host in hosts if host['name'] == selected_host), None)
        if host_data:
            open_workspaces_with_log(selected, host_data['hostname'])

    # Modern styled buttons
    open_button = ttk.Button(button_frame, 
                            text="Open Selected Workspaces",
                            style='Modern.TButton',
                            command=on_open)
    open_button.pack(side="right", padx=5)

    # Make log_message available globally
    globals()['log_message'] = log_message

    # Bind scrolling and resize events
    def on_tree_configure(event=None):
        root.after(10, position_all_checkboxes)
    
    tree.bind('<Configure>', on_tree_configure)
    vsb['command'] = lambda *args: (tree.yview(*args), position_all_checkboxes())
    tree.configure(yscrollcommand=lambda *args: (vsb.set(*args), position_all_checkboxes()))

    # Run the GUI
    root.mainloop()

if __name__ == "__main__":
    main()