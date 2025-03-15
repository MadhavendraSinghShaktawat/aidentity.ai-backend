"""
Script to update dependencies to compatible versions.
"""
import subprocess
import sys

def run_command(command):
    """Run a command and print its output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode

def main():
    """Update dependencies to compatible versions."""
    # Uninstall current versions
    print("Uninstalling current versions...")
    run_command("pip uninstall -y fastapi pydantic pydantic-core")
    
    # Install specific compatible versions
    print("\nInstalling compatible versions...")
    run_command("pip install fastapi==0.95.2 pydantic==1.10.8")
    
    # Show installed versions
    print("\nInstalled versions:")
    run_command("pip show fastapi pydantic")
    
    print("\nDependencies updated successfully!")
    print("Please restart your FastAPI application.")

if __name__ == "__main__":
    main() 