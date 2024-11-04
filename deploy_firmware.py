#!/usr/bin/env python3
import sys
import time
import requests
import logging
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('firmware_deploy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Disable insecure HTTPS warnings if needed
disable_warnings(InsecureRequestWarning)

def create_session():
    """Create a requests session with retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=5)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def check_device_online(ip_address, timeout=2):
    """Check if device is responding to API calls"""
    logger.debug(f"Checking if device {ip_address} is online")
    try:
        session = create_session()
        response = session.get(f'http://{ip_address}/api/system/info', timeout=timeout)
        online = response.status_code == 200
        logger.debug(f"Device {ip_address} online status: {online}")
        return online
    except Exception as e:
        logger.debug(f"Device {ip_address} check failed: {str(e)}")
        return False

def wait_for_device(ip_address, attempts=30, delay=2):
    """Wait for device to come back online"""
    logger.info(f"Waiting for device {ip_address} to become available...")
    for attempt in range(attempts):
        if check_device_online(ip_address):
            logger.info(f"Device {ip_address} is online!")
            # Add an extra small delay to ensure device is fully ready
            time.sleep(2)
            return True
        logger.debug(f"Device not ready, attempt {attempt + 1}/{attempts}")
        time.sleep(delay)
    logger.error(f"Device {ip_address} failed to come back online")
    return False

def upload_file(session, url, file_path, ip_address):
    """Upload a file with detailed logging"""
    logger.info(f"Starting upload to {url}")
    file_size = Path(file_path).stat().st_size
    logger.debug(f"File size: {file_size} bytes")
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/octet-stream',
        'Origin': f'http://{ip_address}',
        'Referer': f'http://{ip_address}/',
        'Connection': 'keep-alive'
    }
    
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        response = session.post(
            url,
            data=file_data,
            headers=headers,
            timeout=60
        )
        
        response.raise_for_status()
        logger.debug(f"Upload response: {response.status_code} - {response.text[:200]}")
        return True
            
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        return False

def update_device(ip_address, firmware_path, www_path):
    """Update a single Bitaxe device with new firmware"""
    logger.info(f"Starting update for device at {ip_address}")
    
    try:
        session = create_session()
        
        # Check initial device status
        if not check_device_online(ip_address):
            logger.error(f"Device {ip_address} not responding to initial check")
            return False
            
        # Upload main firmware
        logger.info(f"Uploading main firmware to {ip_address}")
        if not upload_file(session, f'http://{ip_address}/api/system/OTA', firmware_path, ip_address):
            return False
        logger.info(f"Firmware upload completed for {ip_address}")
        
        # Device will automatically reboot after firmware update
        # Wait for it to come back online
        logger.info("Waiting for device to reboot after firmware update...")
        if not wait_for_device(ip_address):
            logger.error("Device failed to come back online after firmware update")
            return False
        
        # Create new session for WWW upload
        session = create_session()
        
        # Upload www partition
        logger.info(f"Uploading WWW partition to {ip_address}")
        if not upload_file(session, f'http://{ip_address}/api/system/OTAWWW', www_path, ip_address):
            return False
        logger.info(f"WWW partition upload completed for {ip_address}")
        
        # Trigger final reboot
        try:
            logger.info(f"Triggering final reboot for {ip_address}")
            session.post(f'http://{ip_address}/api/system/restart', timeout=5)
        except requests.exceptions.RequestException as e:
            logger.debug(f"Expected disconnect during reboot: {str(e)}")
        
        # Wait for device to come back online after final reboot
        logger.info(f"Waiting for device {ip_address} to complete final reboot...")
        if not wait_for_device(ip_address):
            logger.error("Device failed to come back online after final reboot")
            return False
            
        logger.info(f"Device {ip_address} update completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error updating device {ip_address}: {str(e)}", exc_info=True)
        return False

def main():
    logger.info("Starting firmware deployment script")
    
    if len(sys.argv) != 2:
        logger.error("Invalid arguments")
        print("Usage: deploy_firmware.py IP1,IP2,IP3...")
        sys.exit(1)
        
    # Check firmware files exist
    firmware = Path("ESP-miner/build/esp-miner.bin")
    www = Path("ESP-miner/build/www.bin")
    
    try:
        if not firmware.exists():
            raise FileNotFoundError(f"Firmware file not found at {firmware}")
        if not www.exists():
            raise FileNotFoundError(f"WWW file not found at {www}")
            
        logger.info(f"Found firmware file: {firmware} ({firmware.stat().st_size} bytes)")
        logger.info(f"Found WWW file: {www} ({www.stat().st_size} bytes)")
        
        # Get list of devices
        devices = [ip.strip() for ip in sys.argv[1].strip().split(',')]
        logger.info(f"Deploying to devices: {devices}")
        
        # Update devices sequentially
        results = []
        for device in devices:
            success = update_device(device, firmware, www)
            results.append(success)
        
        # Print summary
        logger.info("\nDeployment Summary:")
        for device, success in zip(devices, results):
            status = "SUCCESS" if success else "FAILED"
            logger.info(f"{device}: {status}")
        
        if not all(results):
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
