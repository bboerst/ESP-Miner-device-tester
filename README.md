# Firmware On-Device Tester

This repository contains GitHub Actions workflows and scripts for automated testing and deployment of [ESP-Miner](https://github.com/skot/ESP-miner) firmware to Bitaxe devices. It allows you to automatically build and deploy firmware updates to a set of test devices whenever changes are detected in the upstream repository.

## Features

- Automated building of ESP-Miner firmware
- Deployment to multiple Bitaxe devices over HTTP
- Periodic checking for upstream changes (every 4 hours)
- Self-hosted runner support for secure device access
- Automatic firmware and WWW partition updates

## Setup Instructions

1. Fork this repository to your GitHub account

2. Set up a self-hosted runner:
   - Go to your forked repository's Settings > Actions > Runners
   - Click "New self-hosted runner"
   - Follow the installation instructions for your platform
   - Add these labels to your runner:
     - `self-hosted`
     - `Linux`
     - `X64`
     - `ESP-Miner-device-tester-repo`

3. Configure repository secrets:
   - Go to Settings > Secrets and variables > Actions
   - Add a new repository secret named `BITAXE_TEST_DEVICES`
   - Value format: comma-separated list of IP addresses, e.g.: `192.168.1.100,192.168.1.101`

4. Install required software on the runner:
   - Python 3.10 or later
   - Node.js 22 or later
   - ESP-IDF v5.3.1
   - Git

## Usage

The workflow can be triggered in three ways:

1. **Automatically every 4 hours**:
   - The workflow checks for new commits in the upstream ESP-Miner repository
   - If new commits are found, it builds and deploys the firmware

2. **On push to master**:
   - Any push to your fork's master branch triggers a build and deploy

3. **Manually**:
   - Go to Actions > Test Deploy to Bitaxe Devices
   - Click "Run workflow"

## Troubleshooting

1. **Build Failures**:
   - Check the build logs in GitHub Actions
   - Verify ESP-IDF version compatibility
   - Ensure all submodules are properly initialized

2. **Deployment Failures**:
   - Verify device IP addresses are correct
   - Check network connectivity from runner to devices
   - Ensure devices are powered on and responsive

3. **Runner Issues**:
   - Verify runner is online and properly labeled
   - Check runner logs for connectivity problems
   - Ensure all required software is installed

## Contributing

Contributions are welcome! Please submit pull requests with any improvements or bug fixes.

## License

This project is licensed under the same terms as the ESP-Miner project, `GNU General Public License v3.0`
