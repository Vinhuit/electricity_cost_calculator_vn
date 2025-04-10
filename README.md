# Electricity Cost Calculator

A Home Assistant custom integration to calculate electricity costs for devices based on their kWh usage, using a tiered pricing structure for Vietnam.

## Features
- Calculates electricity cost for any kWh sensor.
- Supports Vietnam's tiered pricing structure.
- Adds 10% VAT to the final cost.
- Creates two sensors per device: cost without VAT and cost with VAT.

## Installation
1. Install via HACS by adding this repository as a custom repository.
2. Restart Home Assistant.
3. Add the integration via **Settings > Devices & Services > Add Integration**.

## Configuration
- Specify the kWh sensor entity ID (e.g., `sensor.smart_plug_1`).
- Provide a friendly name for the device (e.g., "Smart Plug 1").

## Pricing Structure
- 0–50 kWh: 1,678 VND/kWh
- 51–100 kWh: 1,734 VND/kWh
- 101–200 kWh: 2,014 VND/kWh
- 201–300 kWh: 2,536 VND/kWh
- 301–400 kWh: 2,834 VND/kWh
- 401+ kWh: 2,927 VND/kWh
- 10% VAT is added to the final cost.
