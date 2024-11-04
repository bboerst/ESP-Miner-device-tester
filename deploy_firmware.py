#!/usr/bin/env python3
import sys
import time
import requests
from pathlib import Path

def check_device_online(ip_address, timeout=2):
    try:
        response = requests.get(f'http://{ip_address}/api/system/info', timeout=timeout)
        return response.status_code == 200
    except:
        return False

def update_device(ip_address, firmware_path, www_path):
    """Update a single Bitaxe device with new firmware"""
    print(f"Updating device at {ip_address}")
    
    try:
        # Upload www partition first
        with open(www_path, 'rb') as f:
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/octet-stream',
                'Origin': f'http://{ip_address}',
                'Referer': f'http://{ip_address}/',
                'Connection': 'keep-alive'
            }
            response = requests.post(
                f'http://{ip_address}/api/system/WWW',
                data=f.read(),
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
        print(f"WWW partition uploaded to {ip_address}")

        # Upload main firmware
        with open(firmware_path, 'rb') as f:
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/octet-stream',
                'Origin': f'http://{ip_address}',
                'Referer': f'http://{ip_address}/',
                'Connection': 'keep-alive'
            }
            response = requests.post(
                f'http://{ip_address}/api/system/OTA',
                data=f.read(),
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
        print(f"Firmware uploaded to {ip_address}")
        
        # Trigger reboot
        requests.post(f'http://{ip_address}/api/system/restart', timeout=2)
        print(f"Reboot triggered for {ip_address}")
        
        # Wait for device to come back online
        time.sleep(10)  # Initial wait
        
        for _ in range(5):  # Check a few times
            if check_device_online(ip_address):
                print(f"Device {ip_address} is back online!")
                return True
            time.sleep(5)
        
        print(f"Warning: Could not confirm device {ip_address} is back online")
        return False
        
    except Exception as e:
        print(f"Error updating device {ip_address}: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: deploy_firmware.py IP1,IP2,IP3...")
        sys.exit(1)

    # Check firmware files exist
    firmware = Path("ESP-miner/build/esp-miner.bin")
    www = Path("ESP-miner/build/www.bin")
    if not firmware.exists():
        raise FileNotFoundError(f"Firmware file not found at {firmware}")
    if not www.exists():
        raise FileNotFoundError(f"WWW file not found at {www}")
    
    # Get list of devices
    devices = [ip.strip() for ip in sys.argv[1].strip().split(',')]
    
    # Update devices sequentially
    results = []
    for device in devices:
        success = update_device(device, firmware, www)
        results.append(success)
    
    # Print summary
    print("\nDeployment Summary:")
    for device, success in zip(devices, results):
        status = "SUCCESS" if success else "FAILED"
        print(f"{device}: {status}")
    
    if not all(results):
        sys.exit(1)

if __name__ == "__main__":
    main()
