import os
import subprocess
import sys

def clone_repository():
    repo_url = "https://github.com/hunterricks/happyhouse"
    repo_dir = "happyhouse"
    
    if os.path.exists(repo_dir):
        print(f"Directory '{repo_dir}' already exists. Skipping clone operation.")
        return

    clone_command = ["git", "clone", repo_url]
    
    try:
        subprocess.run(clone_command, check=True)
        print("Repository cloned successfully.")
    except subprocess.CalledProcessError:
        print("Error: Failed to clone the repository.")
        sys.exit(1)

def install_node_and_npm():
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        print("Node.js and npm are already installed.")
    except subprocess.CalledProcessError:
        print("Installing Node.js and npm...")
        subprocess.run(["npm", "install", "-g", "n"], check=True)
        subprocess.run(["n", "lts"], check=True)
        print("Node.js and npm installed successfully.")

def install_react_native_cli():
    try:
        subprocess.run(["npm", "install", "-g", "react-native-cli"], check=True)
        print("React Native CLI installed successfully.")
    except subprocess.CalledProcessError:
        print("Error: Failed to install React Native CLI.")
        sys.exit(1)

def setup_environment():
    try:
        # Change to the happyhouse directory
        os.chdir("happyhouse")
        
        # Install project dependencies
        subprocess.run(["npm", "install"], check=True)
        print("Project dependencies installed successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    clone_repository()
    install_node_and_npm()
    install_react_native_cli()
    setup_environment()
    print("React Native project setup completed. You can now run the project using run.py.")

if __name__ == "__main__":
    main()
