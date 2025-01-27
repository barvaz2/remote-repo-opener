# VSCode Remote Workspace Opener

A tool for opening remote repositories located on various machines directly in Visual Studio Code via SSH. This project simplifies the process of scanning, selecting, and launching `.code-workspace` files from remote servers.

> **Note**: This tool is designed for Windows systems only and requires SSH key authentication.

## Features

- **SSH Integration**: Automatically connects to remote hosts using SSH key authentication and scans for `.code-workspace` files.
- **Easy Workspace Management**: Intuitive GUI for selecting and managing multiple workspaces.
- **Windows Integration**: Seamlessly integrates with Windows' SSH configuration and VSCode.
- **Customizable**: Saves and loads user preferences and workspace selections for quick access.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd <repo-name>
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the script:
   ```bash
   python open_projects.py
   ```

4. Configure the shortcut (optional):
   - Right-click on the `.lnk` shortcut file
   - Select "Properties"
   - In the "Target" field, update the path to match your installation:
     ```
     C:\path\to\your\installation\run_open_projects.vbs
     ```
   - Click "Apply" and "OK"
   - You can drag the shortcut to your taskbar for quick access

## Usage

1. Start the script:
   ```bash
   python open_projects.py
   ```
   Or click the shortcut in your taskbar if configured.

2. Select a remote host from the dropdown menu. The available hosts are retrieved from your `~/.ssh/config` file.
3. The tool will scan the selected host for `.code-workspace` files.
4. Check the workspaces you want to open.
   > **Note**: Your workspace selections are automatically saved and will persist between sessions.
5. Click "Open Selected Workspaces" to launch them in Visual Studio Code.