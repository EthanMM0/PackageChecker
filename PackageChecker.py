import os
import sys
import importlib
import subprocess
import ctypes
import yaml  # Import after ensuring installation

# List of required external packages
required_packages = {"yaml": "PyYAML"}  # Mapping import name to pip package name

# Function to check if a package is installed
def is_installed(package_name):
    try:
        module = importlib.import_module(package_name)
        return True, getattr(module, '__version__', 'unknown version')
    except ImportError:
        return False, None

# Function to install a package
def install_package(pip_name):
    print(f"Package: {pip_name} is installing")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Package: {pip_name} Installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing {pip_name}: {e}")
        return False

# Ensure required packages are installed
for import_name, pip_name in required_packages.items():
    installed, _ = is_installed(import_name)
    if not installed:
        install_package(pip_name)

# Function to find all imported packages in the current project
def find_imported_packages():
    imported_packages = set()
    for root, _, files in os.walk('.'):  # Scan current directory
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r') as f:
                    for line in f:
                        if line.startswith('import') or line.startswith('from'):
                            parts = line.split()
                            if parts[0] == 'import':
                                imported_packages.add(parts[1].split('.')[0])
                            elif parts[0] == 'from':
                                imported_packages.add(parts[1].split('.')[0])
    return imported_packages

# Prompt user for confirmation
def prompt_user_confirmation(message):
    response = ctypes.windll.user32.MessageBoxW(0, message, "Confirmation", 1)
    return response == 1

# Function to display completion alert
def show_completion_alert(installed_packages):
    if not installed_packages:
        message = "All packages are already installed correctly."
    else:
        message = "Dependencies Installed:\n" + "\n".join(installed_packages)
    ctypes.windll.user32.MessageBoxW(0, message, "Installation Complete", 0)

# Main function
def main():
    packages = find_imported_packages()
    dependencies = {}
    missing_packages = []
    
    # Save initial package list to YAML
    with open('Dependencies.yaml', 'w') as yaml_file:
        yaml.dump({pkg: "Unchecked" for pkg in packages}, yaml_file, default_flow_style=False)
    
    if not prompt_user_confirmation("Would you like to check for missing packages in the project?"):
        print("Installation canceled.")
        return

    for package in packages:
        installed, version = is_installed(package)
        if installed:
            print(f"Package: {package} is already installed")
            dependencies[package] = f"Installed ({version})"
        else:
            missing_packages.append(f"{package}: {version if version else 'Unknown Version'}")
            dependencies[package] = "Not Installed"
    
    # Save updated dependencies
    with open('Dependencies.yaml', 'w') as yaml_file:
        yaml.dump(dependencies, yaml_file, default_flow_style=False)
    
    if not missing_packages:
        show_completion_alert([])
        return
    
    # Ask user if they want to install missing packages
    missing_packages_message = "List of missing packages:\n" + "\n".join(missing_packages) + "\n\nWould you like to install them?"
    if not prompt_user_confirmation(missing_packages_message):
        print("Installation of missing packages canceled.")
        return
    
    installed_packages = []
    for package_info in missing_packages:
        package_name = package_info.split(':')[0]
        success = install_package(package_name)
        if success:
            installed, version = is_installed(package_name)
            dependencies[package_name] = f"Installed ({version})" if installed else "Failed"
            if installed:
                installed_packages.append(f"{package_name}: {version}")
    
    # Save final updated dependencies
    with open('Dependencies.yaml', 'w') as yaml_file:
        yaml.dump(dependencies, yaml_file, default_flow_style=False)
    
    # Show completion alert
    show_completion_alert(installed_packages)

if __name__ == "__main__":
    main()