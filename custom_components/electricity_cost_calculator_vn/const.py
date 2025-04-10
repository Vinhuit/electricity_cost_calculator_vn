DOMAIN = "electricity_cost_calculator_vn"

# Configuration keys
CONF_KWH_SENSOR = "kwh_sensor"
CONF_POWER_SENSOR = "power_sensor"
CONF_CURRENT_SENSOR = "current_sensor"
CONF_VOLTAGE_SENSOR = "voltage_sensor"
CONF_DEVICE_NAME = "device_name"
CONF_TIER_1_RATE = "tier_1_rate"  # 0–50 kWh
CONF_TIER_2_RATE = "tier_2_rate"  # 51–100 kWh
CONF_TIER_3_RATE = "tier_3_rate"  # 101–200 kWh
CONF_TIER_4_RATE = "tier_4_rate"  # 201–300 kWh
CONF_TIER_5_RATE = "tier_5_rate"  # 301–400 kWh
CONF_TIER_6_RATE = "tier_6_rate"  # 401+ kWh
CONF_VAT_RATE = "vat_rate"  # VAT percentage
CONF_COST_UNIT = "cost_unit"  # Currency unit for cost

# Default values (used as fallback in Config Flow)
DEFAULT_TIER_1_RATE = 1678
DEFAULT_TIER_2_RATE = 1734
DEFAULT_TIER_3_RATE = 2014
DEFAULT_TIER_4_RATE = 2536
DEFAULT_TIER_5_RATE = 2834
DEFAULT_TIER_6_RATE = 2927
DEFAULT_VAT_RATE = 0.1  # 10%
DEFAULT_COST_UNIT = "VND"

# Sensor suffixes
SENSOR_COST = "electricity_cost"
SENSOR_COST_WITH_VAT = "electricity_cost_with_vat"