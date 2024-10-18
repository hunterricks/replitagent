import os
import subprocess
import logging
import psutil
import socket
import shutil

def check_common_issues():
    issues = []
    
    if is_port_in_use(19000):
        issues.append("Port 19000 is already in use. We'll try to find an available port.")
    
    try:
        subprocess.run(["npm", "list", "expo", "react", "react-native"], 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL, 
                       check=True)
    except subprocess.CalledProcessError:
        issues.append("Some required dependencies (expo, react, react-native) may be missing. Please run 'npm install' in the project directory.")
    
    if not check_disk_space("."):
        issues.append("Low disk space detected. This may cause issues with Metro bundler.")
    
    if not check_system_resources():
        issues.append("System resources (CPU or memory) are running low. This may affect Expo server performance.")

    return issues

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port, end_port):
    for port in range(start_port, end_port + 1):
        if not is_port_in_use(port):
            return port
    return None

def check_disk_space(path, required_space_gb=1):
    usage = psutil.disk_usage(path)
    free_space_gb = usage.free // (2**30)
    if free_space_gb < required_space_gb:
        logging.warning(f"Low disk space: {free_space_gb}GB free. At least {required_space_gb}GB recommended.")
        return False
    return True

def check_system_resources():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    
    logging.info(f"CPU usage: {cpu_percent}%")
    logging.info(f"Memory usage: {memory_percent}%")
    
    if cpu_percent > 80:
        logging.warning(f"High CPU usage: {cpu_percent}%. This may affect Expo server performance.")
    if memory_percent > 80:
        logging.warning(f"High memory usage: {memory_percent}%. This may affect Expo server performance.")
    
    return cpu_percent < 90 and memory_percent < 90

def clear_metro_bundler_cache():
    try:
        subprocess.run(["npx", "react-native", "start", "--reset-cache"], check=True, timeout=60)
        logging.info("Metro bundler cache cleared successfully.")
    except subprocess.CalledProcessError:
        logging.error("Failed to clear Metro bundler cache.")
    except subprocess.TimeoutExpired:
        logging.error("Timeout while clearing Metro bundler cache.")

def clear_metro_bundler_cache_alternative():
    try:
        cache_dir = os.path.expanduser("~/.metro")
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            logging.info("Metro bundler cache cleared using alternative method.")
        else:
            logging.info("No Metro bundler cache found to clear.")
    except Exception as e:
        logging.error(f"Failed to clear Metro bundler cache using alternative method: {str(e)}")

def reduce_memory_usage():
    try:
        subprocess.run(["npm", "cache", "clean", "--force"], check=True)
        logging.info("npm cache cleaned successfully.")
    except subprocess.CalledProcessError:
        logging.error("Failed to clean npm cache.")
