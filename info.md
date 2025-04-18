# ha-venta: Venta Integration for Home Assistant

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/integration)

This is a custom integration for [Home Assistant](https://www.home-assistant.io/) allowing control over Venta air treatment devices equipped with a Wi-Fi module. It supports devices communicating via Venta protocols v0, v2, and v3.

---

**❗ IMPORTANT: Venta Device Compatibility Notice (Updated April 2025)**

Please be aware that many Venta devices, **especially those manufactured since late 2024** (including potentially older models), are now exclusively using Tuya-based infrastructure.

**These Tuya-based devices are NOT compatible with this `ha-venta` integration.**

It is highly likely that future Venta devices and firmware revisions will continue this trend.

**How to check?** If your device setup relies solely on the "Tuya Smart" / "Smart Life" app and does not involve the older "Venta Control" app or direct local network discovery identifiable by this integration, it's likely Tuya-based.

**If your device uses Tuya:** Please use alternative Home Assistant integrations:
* **Local Control:** [LocalTuya](https://github.com/rospogrigio/localtuya) (Requires retrieving local keys)
* **Cloud Control:** Official [Tuya Integration](https://www.home-assistant.io/integrations/tuya/)

For further discussion on identifying compatible models, see [Discussion #77](https://github.com/Michsior14/ha-venta/discussions/77).

---

## Supported Devices & Protocols

This integration has been tested with the following models based on their underlying Venta communication protocol:

* **Protocol v0:**
    * LP60 / LPH60
    * LW60 / LW60T
    * LW62 / LW62T
    * AP902 / AH902 / AW902
* **Protocol v2:**
    * LW73 / LW74
    * LP73 / LP74
* **Protocol v3:**
    * AS100 / AS150
    * AH510 / AH515 / AH530 / AH535 / AH550 / AH555

*(If your device works and isn't listed, please consider reporting it via a GitHub Issue!)*

## Features

* **Humidifier Control:**
    * Set Fan Speed / Level
    * Set Target Humidity (%)
    * Toggle Auto Mode
    * Toggle Sleep Mode
* **LED Strip Control:** (If applicable to model)
    * Turn On/Off
    * Set Color
    * Set Mode (e.g., cycle)
* **Sensors:**
    * Water Level
    * Current Humidity
    * Current Temperature
    * Service/Cleaning Reminders (Time remaining)
    * Device Status & Errors

## Prerequisites

1.  **Device Setup:** Your Venta device must be successfully set up using the appropriate Venta mobile app (potentially the older "Venta Control" app for non-Tuya devices) and connected to your local Wi-Fi network.
2.  **Static IP Address (Recommended):** Assign a static IP address or DHCP reservation to your Venta device via your router settings. This prevents connection issues if the device's IP changes. Note down this IP address.

## Installation

### Method 1: HACS (Recommended)

1.  Ensure [HACS (Home Assistant Community Store)](https://hacs.xyz/) is installed.
2.  Navigate to HACS -> Integrations.
3.  Click the "+ Explore & Download Repositories" button.
4.  Search for "Venta".
5.  Select the "Venta" integration and click "Download".
6.  Restart Home Assistant.

### Method 2: Manual Installation

1.  Download the latest release (`Source code (zip)`) from the [Releases page](https://github.com/Michsior14/ha-venta/releases). 2.  Unzip the downloaded file.
3.  Locate the `venta` directory inside the unzipped folder (it should contain files like `manifest.json`, `__init__.py`, etc.).
4.  Copy the entire `venta` directory into your Home Assistant's `<config>/custom_components/` directory. If the `custom_components` directory doesn't exist, create it.
    * Common paths for `<config>`:
        * Home Assistant OS/Supervised: `/config` or `/usr/share/hassio/homeassistant`
        * Home Assistant Core (venv/docker): The directory where your `configuration.yaml` is located.
5.  Restart Home Assistant.

## Configuration

Once installed, the Venta integration can be added via the Home Assistant UI:

1.  Go to **Settings** -> **Devices & Services**.
2.  Click the **+ ADD INTEGRATION** button.
3.  Search for "Venta" and select it.
4.  A configuration dialog will appear. Enter the **IP address** of your Venta device (the one you noted down in Prerequisites).
5.  Click **Submit**.

The integration will attempt to connect to the device and automatically add the corresponding entities to Home Assistant.

## Contributing

Contributions are welcome!

### Translations

Help translate the integration into more languages! We use [Lokalise](https://app.lokalise.com/public/2728010065b52d190d6247.58782749/) for translation management. Feel free to contribute there.

## Disclaimer

This is a third-party integration developed independently from Venta. Use it at your own risk. The developers are not responsible for any damage or issues caused by using this software.