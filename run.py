import os
import subprocess
import sys
import time
import re

def generate_qr_code(url):
    try:
        import qrcode
        from io import BytesIO
        from PIL import Image

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to a file
        img.save("expo_qr_code.png")
        print("QR code saved as expo_qr_code.png")
        
        # Display ASCII QR code in the console
        f = BytesIO()
        img.save(f, "PNG")
        f.seek(0)
        w, h = img.size
        print("\nScan this QR code with the Expo Go app:")
        for y in range(h):
            print("".join("██" if img.getpixel((x, y)) < 128 else "  " for x in range(w)))
    except ImportError:
        print("Unable to generate QR code. Please install 'qrcode' and 'pillow' libraries.")
        print(f"Expo URL: {url}")

def run_project():
    try:
        os.chdir("happyhouse")
        
        print("Starting Expo development server for mobile...")
        
        process = subprocess.Popen(
            ["npx", "expo", "start", "--port", "19000"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        start_time = time.time()
        port_pattern = re.compile(r'(exp://.*:\d+)')
        url_found = False
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                port_match = port_pattern.search(output)
                if port_match and not url_found:
                    url = port_match.group(1)
                    print(f"Expo development server is running on {url}")
                    print("To run on iOS simulator: expo run:ios")
                    print("To run on Android emulator: expo run:android")
                    print("To run on physical device, scan the QR code with the Expo Go app")
                    generate_qr_code(url)
                    url_found = True
                elif "Starting project" in output:
                    print("Expo is starting, waiting for URL information...")
            
            if time.time() - start_time > 900:  # 15 minutes timeout
                print("Timeout: Expo development server did not provide URL information within 15 minutes.")
                break
            
            if time.time() - start_time > 300 and (int(time.time() - start_time) % 60 == 0):
                print(f"Still waiting for URL information... ({int((time.time() - start_time) / 60)} minutes elapsed)")
        
        if not url_found:
            print("Error: Expo development server failed to provide URL information.")
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
