# EX-HABridge Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Custom integration that allows [Home Assistant](https://www.home-assistant.io/) to control and monitor an [EX-CommandStation](https://dcc-ex.com/ex-commandstation/index.html) — a simple but powerful DCC/DC command station used for running model train layouts.


## ✅ Planned and Implemented Features

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

### CV Operations

- [x] Write to CV registers via service
- [ ] Read CV registers via service
- [ ] Display CV read results

## Installation using HACS

To install the EX-HABridge integration using [HACS](https://hacs.xyz/), follow these steps:
1. Open Home Assistant and navigate to **HACS**.
2. Click on 3 dots in the top right corner and select **Custom repositories**.
3. Fill in the form and click **Add**:
   - **Repository**: `https://github.com/SenMorgan/EX-HABridge`
   - **Type**: `Integration`
4. Once added, go back to **Integrations** in HACS, search for *EX-HABridge*, and click the **DOWNLOAD** button.
5. After the download is complete, restart Home Assistant.
6. Go to **Settings** > **Devices & Services** and click on **Add Integration**.
7. Search for *EX-HABridge* and follow the prompts to configure the integration.

## Disclaimer

This integration is an unofficial, community-developed project and is not affiliated with or officially endorsed by Home Assistant or the DCC-EX project. Use at your own risk.

The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the author(s) be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

All trademarks and logos are property of their respective owners.

## License

Copyright (c) 2025 Arsenii Kuzin (aka Sen Morgan). Licensed under the MIT license, see LICENSE.md
