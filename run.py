import os
import subprocess
import sys
import time
import re

def run_project():
    try:
        os.chdir("happyhouse")
        
        print("Starting React Native development server...")
        
        process = subprocess.Popen(
            ["npx", "react-native", "start"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        process.stdin.write('y\n')
        process.stdin.flush()
        
        start_time = time.time()
        port_pattern = re.compile(r'Metro waiting on (\d+)')
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                port_match = port_pattern.search(output)
                if port_match:
                    port = port_match.group(1)
                    print(f"React Native development server is running on port {port}.")
                    return
                elif "Running Metro" in output:
                    print("Metro bundler is running, waiting for port information...")
            
            if time.time() - start_time > 600:  # Increased timeout to 10 minutes
                print("Timeout: React Native development server did not provide port information within 10 minutes.")
                break
        
        print("Error: React Native development server failed to start properly or provide port information.")
        print("Checking for error messages...")
        
        error_output = process.stderr.read()
        if error_output:
            print("Error output:")
            print(error_output)
        
        if process.returncode is not None and process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, process.args)
        
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    run_project()

if __name__ == "__main__":
    main()
