DOMAIN = "electricity_cost_calculator"

# Configuration keys
CONF_KWH_SENSOR = "kwh_sensor"
CONF_DEVICE_NAME = "device_name"

# Tiered pricing structure (VND/kWh)
TIER_1_RATE = 1678  # 0–50 kWh
TIER_2_RATE = 1734  # 51–100 kWh
TIER_3_RATE = 2014  # 101–200 kWh
TIER_4_RATE = 2536  # 201–300 kWh
TIER_5_RATE = 2834  # 301–400 kWh
TIER_6_RATE = 2927  # 401+ kWh

# VAT rate
VAT_RATE = 0.1  # 10%

# Sensor suffixes
SENSOR_COST = "electricity_cost"
SENSOR_COST_WITH_VAT = "electricity_cost_with_vat"