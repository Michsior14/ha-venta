"""Constants for the Venta integration."""

from homeassistant.components.humidifier import (
    MODE_AUTO,
)

DOMAIN = "venta"
CONF_API_DEFINITION_ID = "api_definition_id"

AUTO_API_VERSION = "auto"
DEFAULT_SCAN_INTERVAL = 10
NO_WATER_THRESHOLD = 50000

MODE_SLEEP = "sleep"
MODE_TURBO = "turbo"
MODE_LEVEL_1 = "level_1"
MODE_LEVEL_2 = "level_2"
MODE_LEVEL_3 = "level_3"
MODE_LEVEL_4 = "level_4"
MODE_LEVEL_5 = "level_5"

MODES_3: list[str] = [
    MODE_AUTO,
    MODE_LEVEL_1,
    MODE_LEVEL_2,
    MODE_LEVEL_3,
]
MODES_4: list[str] = [
    *MODES_3,
    MODE_LEVEL_4,
]
MODES_5: list[str] = [
    *MODES_4,
    MODE_LEVEL_5,
]

ATTR_HUMIDITY = "humidity"
ATTR_WATER_LEVEL = "water_level"
ATTR_FAN_SPEED = "fan_speed"
ATTR_OPERATION_TIME = "operation_time"
ATTR_DISC_ION_TIME = "disc_ion_time"
ATTR_DISC_ION_TIME_TO_REPLACE = "disc_ion_time_to_replace"
ATTR_CLEANING_TIME = "cleaning_time"
ATTR_TIME_TO_CLEAN = "time_to_clean"
ATTR_SERVICE_TIME = "service_time"
ATTR_TIME_TO_SERVICE = "time_to_service"
ATTR_SERVICE_MAX_TIME = "service_max_time"
ATTR_WARNINGS = "warnings"
ATTR_PARTICLES_0_3 = "particles_0_3"
ATTR_PARTICLES_0_5 = "particles_0_5"
ATTR_PARTICLES_1_0 = "particles_1_0"
ATTR_PARTICLES_2_5 = "particles_2_5"
ATTR_PARTICLES_5_0 = "particles_5_0"
ATTR_PARTICLES_10 = "particles_10"
ATTR_PM_1_0 = "pm_1_0"
ATTR_PM_2_5 = "pm_2_5"
ATTR_PM_10 = "pm_10"
ATTR_VOC = "voc"
ATTR_HCHO = "hcho"
ATTR_CO2 = "co2"
ATTR_DUST = "dust"
ATTR_NEEDS_REFILL = "needs_refill"
ATTR_NEEDS_SERVICE = "needs_service"
ATTR_NEEDS_DISC_REPLACEMENT = "needs_disc_replacement"
ATTR_NEEDS_CLEANING = "needs_cleaning"
ATTR_CLEANING="cleaning"

ATTR_LED_STRIP = "led_strip"
ATTR_LED_STRIP_MODE = "led_strip_mode"
ATTR_SLEEP_MODE = "sleep_mode"

ION_DISC_REPLACE_TIME_DAYS = 121  # max seen value 17426 ~ 121 days
CLEAN_TIME_DAYS = 182  # max seen value 26210 ~ 182 days
SERVICE_TIME_DAYS = 14  # max seen value 2018 ~ 14 days
FILTER_TIME_DAYS = 182  # max seen value 26210 ~ 182 days
