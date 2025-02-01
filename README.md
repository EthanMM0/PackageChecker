# PackageChecker

## **This code does the following:**

- Checks if the user has `yaml` and installs it if not (important to run the code).
  - Then it prompts the user if they want to check if they have missing project dependencies.
    - It will list all the packages in `Dependencies.yaml`.
- If the user clicks **Cancel**, it stops the code.
- If confirmed:  
  - It runs:  
    ```bash
    (sys.executable -> (Your Python exe)) -m pip install [package name]
    ```
    for each dependency in the project.

- If all packages are installed:
  - It will open a confirmation alert that says **"All packages are installed correctly."**

- If dependencies are missing:
  - It will list all missing dependencies.
    - Then prompt the user again if they would like to install the list of missing dependencies.
  - If the user clicks **Cancel**, it stops the code.
  - If confirmed:
    - It will install all the missing dependencies.

### **When completed:**
- Prompts the user with a confirmation alert showcasing which packages were installed.
- Updates `Dependencies.yaml` with the installed version (if known).
