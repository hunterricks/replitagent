import os
import subprocess
import sys
import logging
import time
import socket
import psutil

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def find_available_port(start_port, end_port):
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return None

def check_system_resources():
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    logging.info(f"CPU usage: {cpu_usage}%")
    logging.info(f"Memory usage: {memory_usage}%")
    logging.info(f"Disk usage: {disk_usage}%")
    if cpu_usage > 90 or memory_usage > 90 or disk_usage > 90:
        logging.warning("High system resource usage detected!")

def run_project():
    try:
        project_dir = os.path.abspath(os.path.join(os.getcwd(), "happyhouse"))
        os.chdir(project_dir)
        logging.info(f"Changed to directory: {os.getcwd()}")
        
        check_system_resources()
        
        logging.info("Finding available port for Expo development server...")
        port = find_available_port(19000, 19100)
        if not port:
            raise RuntimeError("Unable to find an available port between 19000 and 19100.")
        
        logging.info(f"Starting Expo development server on port {port}...")
        
        env = os.environ.copy()
        env["EXPO_DEBUG"] = "true"
        env["EXPO_METRO_MAX_WORKERS"] = "2"
        env["NODE_OPTIONS"] = "--max-old-space-size=512"
        
        process = subprocess.Popen(
            ["npx", "expo", "start", "--port", str(port), "--no-dev", "--minify"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        start_time = time.time()
        timeout_duration = 300  # 5 minutes timeout
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logging.info(output.strip())
                if "Expo DevTools is running at" in output:
                    logging.info(f"Expo development server started successfully on port {port}")
                    return
            
            error_output = process.stderr.readline()
            if error_output:
                logging.error(f"Error: {error_output.strip()}")
                if "ENOSPC" in error_output:
                    logging.error("File watcher limit reached. Trying to increase the limit...")
                    subprocess.run(["sudo", "sysctl", "-w", "fs.inotify.max_user_watches=524288"], check=True)
                elif "store.clear is not a function" in error_output:
                    logging.error("Metro bundler cache error. Trying to clear the cache...")
                    subprocess.run(["npx", "react-native", "start", "--reset-cache"], check=True)
            
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_duration:
                raise TimeoutError(f"Timeout: Expo development server did not start within {timeout_duration} seconds.")
            
            if int(elapsed_time) % 30 == 0:  # Check system resources every 30 seconds
                check_system_resources()
        
        raise RuntimeError("Expo development server failed to start")
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        logging.error("Stack trace:", exc_info=True)
        sys.exit(1)

def main():
    run_project()

if __name__ == "__main__":
    main()
