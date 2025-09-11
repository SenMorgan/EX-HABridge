# EX-HABridge Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)
![GitHub all releases](https://img.shields.io/github/downloads/SenMorgan/EX-HABridge/total?style=flat-square)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/SenMorgan/EX-HABridge/validate.yml?style=flat-square)

Custom integration that allows [Home Assistant](https://www.home-assistant.io/) to control and monitor an [EX-CommandStation](https://dcc-ex.com/ex-commandstation/index.html) — a simple but powerful DCC/DC command station used for running model train layouts.

<img width="994" height="256" alt="logo" src="https://github.com/user-attachments/assets/56fb0bda-11a1-4ffb-a0a3-ed767d4220e4" />

## Installation using HACS

To install the EX-HABridge integration using [HACS](https://hacs.xyz/), follow these steps:
1. Open Home Assistant and navigate to **HACS**.
2. Click on search field and type ***EX-HABridge***.
3. Click the **DOWNLOAD** button to install the integration.
4. After the download is complete, restart Home Assistant.
5. Go to **Settings** > **Devices & services** and click on **Add integration**.
6. Search for ***EX-HABridge*** and follow the prompts to configure the integration.

## Implemented and Planned Features

### Core

- [x] Communication with EX-CommandStation over Telnet
- [x] Configuration via UI with connection validation
- [x] EX-CommandStation version validation
- [x] Reconnect logic with backoff (device availability monitoring)

### Switches & Controls

- [x] Tracks power toggle (common for Main and Program tracks)
- [x] Support for loco function commands control (using service calls)
- [x] Loco speed and direction control
- [x] Multi-locomotive support
- [x] Turnout control
- [x] Routes/automations control
- [ ] Turntable control

### Other Features

- [x] Automatic assignment of icons to functions based on their names
- [x] Write to CV registers via service
- [ ] Read CV registers via service
- [ ] Display CV read results

## Disclaimer

This integration is an unofficial, community-developed project and is not affiliated with or officially endorsed by Home Assistant or the DCC-EX project. Use at your own risk.

The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the author(s) be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

All trademarks and logos are property of their respective owners.

## License

Copyright (c) 2025 Arsenii Kuzin (aka Sen Morgan). Licensed under the MIT license, see LICENSE.md
