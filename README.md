# ha-venta

A Home Assistant custom Integration for Venta devices (protocol: v0, v2, v3) with wifi module.

The following Venta device are currently tested and supported:

- **Protocol v0:**
  - LP60/LPH60
  - LW60/LW60T
  - LW62/LW62T
  - AP902/AH902/AW902

- **Protocol v2:**
  - LW73/LW74
  - LP73/LP74

- **Protocol v3:**
  - AS100/AS150
  - AH510/AH515/AH530/AH535/AH550/AH555

The new Venta devices like AH730 are using tuya infrastructure exclusively and are **not supported** by this project. If you have such device, please use [local](https://github.com/rospogrigio/localtuya) or [official](https://www.home-assistant.io/integrations/tuya/) Tuya integration.

## Features

- Humidifier control (fan speed, target humidity, and auto/sleep mode).
- LED strip control (on/off, color, mode).
- Diagnostic sensors (water level, temperature, cleaning time, etc.).

## Installation

The easiest way, if you are using [HACS](https://hacs.xyz/), is to install Venta through HACS.

For manual installation, copy the venta folder and all of its contents into your Home Assistant's custom_components folder. This folder is usually inside your `/config` folder. If you are running Hass.io, use SAMBA to copy the folder over. If you are running Home Assistant Supervised, the custom_components folder might be located at `/usr/share/hassio/homeassistant`. You may need to create the `custom_components` folder and then copy the venta folder and all of its contents into it.

## Usage

Before the next steps make sure the device is configured using the Venta Home app and connected to the network. Note down it's IP address.

### Adding the Integration

To start configuring the integration, just press the "+ADD INTEGRATION" button in the Settings - Integrations page, and select Venta from the drop-down menu.
The configuration page will appear, requesting to input ip of the device.

## Translations

Translations are managed via [Lokalise](https://app.lokalise.com/public/2728010065b52d190d6247.58782749/). Feel free to contribute over there!

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
