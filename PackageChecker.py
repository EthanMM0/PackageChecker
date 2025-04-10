import os
import sys
import importlib
import subprocess
import ctypes
import pkgutil
import builtins
import json
import re
from packaging.version import parse as parse_version

# Required for YAML file output
required_packages = {"yaml": "PyYAML"}

# Known deprecated PyPI aliases
deprecated_aliases = {
    "sklearn": "scikit-learn"
}

# Compatibility rules: {package: (affected_package, max_version)}
compatibility_rules = {
    "numpy": [
        ("scipy", "1.27.0"),
        ("pandas", "3.0.0"),
        ("scikit-learn", "1.4.0")
    ]
}

def is_installed(package_name):
    try:
        module = importlib.import_module(package_name)
        return True, getattr(module, '__version__', 'unknown version')
    except ImportError:
        return False, None

def get_available_versions(pip_name):
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'index', 'versions', pip_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    matches = re.findall(rf'{pip_name} \((.*?)\)', result.stdout)
    if matches:
        versions = matches[0].split(', ')
        return [v.strip() for v in versions if re.match(r'^\d', v)]
    return []

def get_latest_compatible_version(package, installed_dependencies):
    versions = get_available_versions(package)
    if not versions:
        return None
    for version in versions:
        compatible = True
        for dep, max_version in compatibility_rules.get(package, []):
            if dep in installed_dependencies:
                if parse_version(version) >= parse_version(max_version):
                    compatible = False
                    break
        if compatible:
            return version
    return None

def install_specific_version(package, version):
    print(f"Installing {package}=={version} for compatibility...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", f"{package}=={version}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    if "deprecated" in result.stdout.lower() or "use 'scikit-learn'" in result.stdout.lower():
        print(f"⚠️ {package} is deprecated.")
        return "DEPRECATED"
    return result.returncode == 0

def prompt_user_confirmation(message):
    response = ctypes.windll.user32.MessageBoxW(0, message, "Confirmation", 1)
    return response == 1

def show_completion_alert(installed_packages):
    if not installed_packages:
        message = "All packages are already installed correctly."
    else:
        message = "Dependencies Installed:\n" + "\n".join(installed_packages)
    ctypes.windll.user32.MessageBoxW(0, message, "Installation Complete", 0)

def is_standard_or_builtin(module_name):
    return (
        module_name in sys.builtin_module_names or
        module_name in dir(builtins) or
        pkgutil.find_loader(module_name) is None
    )

def is_local_module(module_name):
    return os.path.isfile(f"{module_name}.py") or os.path.isdir(module_name)

def find_imported_packages():
    imported_packages = set()
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('import') or line.strip().startswith('from'):
                            parts = line.split()
                            if parts[0] == 'import':
                                imported_packages.add(parts[1].split('.')[0])
                            elif parts[0] == 'from':
                                imported_packages.add(parts[1].split('.')[0])
    return imported_packages

def check_for_updates(packages):
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json'],
        stdout=subprocess.PIPE,
        text=True
    )
    outdated = json.loads(result.stdout)
    updates = {}
    for pkg in outdated:
        name = pkg['name']
        if name.lower() in (p.lower() for p in packages):
            updates[name] = {
                "current": pkg["version"],
                "latest": pkg["latest_version"]
            }
    return updates

def main():
    packages = find_imported_packages()
    dependencies = {}
    external_packages = []
    compatible_installs = []
    installed_dependencies = {}

    # Placeholder YAML
    with open('Dependencies.yaml', 'w') as yaml_file:
        import yaml
        yaml.dump({pkg: "Unchecked" for pkg in packages}, yaml_file, default_flow_style=False)

    if not prompt_user_confirmation("Would you like to check for and install compatible versions of all used packages?"):
        print("Operation cancelled.")
        return

    for package in packages:
        base_package = deprecated_aliases.get(package, package)

        if is_local_module(package):
            dependencies[package] = "Local Module"
        elif is_standard_or_builtin(package):
            dependencies[package] = "Built-in"
        else:
            installed, version = is_installed(package)
            if installed:
                dependencies[package] = version
                installed_dependencies[base_package] = version
                external_packages.append(base_package)
            else:
                external_packages.append(base_package)

    for package in external_packages:
        alias = deprecated_aliases.get(package, package)

        latest_compatible = get_latest_compatible_version(alias, installed_dependencies)

        if not latest_compatible:
            print(f"❌ No compatible version found for {package}")
            dependencies[package] = "Unknown --NO_COMPAT_VERSION"
            continue

        result = install_specific_version(alias, latest_compatible)
        if result == "DEPRECATED":
            dependencies[package] = f"{latest_compatible} --DEPRECATED"
        elif result:
            dependencies[package] = f"{latest_compatible} --COMPATIBLE"
            compatible_installs.append(f"{package}: {latest_compatible}")
        else:
            dependencies[package] = f"{latest_compatible} --FAILED"

    # Save final version list
    with open('Dependencies.yaml', 'w') as yaml_file:
        yaml.dump(dependencies, yaml_file, default_flow_style=False)

    show_completion_alert(compatible_installs)

if __name__ == "__main__":
    for import_name, pip_name in required_packages.items():
        installed, _ = is_installed(import_name)
        if not installed:
            subprocess.run([sys.executable, "-m", "pip", "install", pip_name])

    import yaml
    main()
