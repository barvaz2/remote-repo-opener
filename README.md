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

## Usage

1. Start the script:
   ```bash
   python open_projects.py
   ```

2. Select a remote host from the dropdown menu. The available hosts are retrieved from your `~/.ssh/config` file.
3. The tool will scan the selected host for `.code-workspace` files.
4. Check the workspaces you want to open.
5. Click "Open Selected Workspaces" to launch them in Visual Studio Code.

## Configuration

### SSH Config
Ensure your SSH connections are properly set up in `~/.ssh/config` with SSH key authentication. Example:
```plaintext
Host remote-server
    HostName 192.168.1.100
    User your-username
    PreferredAuthentications publickey
    IdentityFile "C:/Users/your-username/.ssh/id_rsa"
```

> **Important**: Password authentication is not supported. You must use SSH key authentication.

### Settings File
The application saves user preferences and workspace selections in `~/.vscode_workspace_opener_settings.json`. This includes:
- Previously selected workspaces
- Last used remote host
- Custom user settings

## Examples

### Example SSH Config
```plaintext
Host dev-server
    HostName 192.168.1.100
    User developer
    IdentityFile ~/.ssh/id_rsa
```

### Example Output

#### Log Panel:
```plaintext
Scanning workspaces on dev-server...
Found: /home/developer/project1/project1.code-workspace
Found: /home/developer/project2/project2.code-workspace
Opening: code --remote ssh-remote+dev-server /home/developer/project1/project1.code-workspace
```

#### Workspace GUI: 
A list of all `.code-workspace` files with checkboxes for selection.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

This project is released under the Unlicense. It is free and unencumbered software released into the public domain.

