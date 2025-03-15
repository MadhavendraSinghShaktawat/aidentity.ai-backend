"""
Script to check what process is using port 8000.
"""
import subprocess
import sys
import os

def check_port_usage(port):
    """Check what process is using the specified port."""
    try:
        # For Windows
        if sys.platform.startswith('win'):
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(f"Port {port} is in use:")
                print(result.stdout)
                
                # Extract PID
                lines = result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split()
                    if len(parts) >= 5:
                        pid = parts[4]
                        print(f"\nProcess ID: {pid}")
                        
                        # Get process name
                        task_result = subprocess.run(
                            f'tasklist /fi "PID eq {pid}"',
                            shell=True,
                            capture_output=True,
                            text=True
                        )
                        print("\nProcess details:")
                        print(task_result.stdout)
            else:
                print(f"Port {port} is not in use.")
        
        # For Unix-like systems
        else:
            result = subprocess.run(
                f'lsof -i :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(f"Port {port} is in use:")
                print(result.stdout)
            else:
                print(f"Port {port} is not in use.")
    
    except Exception as e:
        print(f"Error checking port usage: {e}")

if __name__ == "__main__":
    port = 8000
    print(f"Checking usage of port {port}...")
    check_port_usage(port)
    
    # Also check if we can bind to the port
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', port))
        print(f"\nSuccessfully bound to port {port}. The port is available.")
        s.close()
    except Exception as e:
        print(f"\nFailed to bind to port {port}: {e}")
        print("The port is in use or not available.") 