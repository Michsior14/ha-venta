"""Constants for the Venta integration."""

from homeassistant.components.humidifier import (
    MODE_AUTO,
)

DOMAIN = "venta"
CONF_API_DEFINITION_ID = "api_definition_id"

AUTO_API_VERSION = "auto"
DEFAULT_SCAN_INTERVAL = 10
NO_WATER_THRESHOLD = 50000

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

WATER_LEVEL_NO_VALUE = "0"
WATER_LEVEL_YELLOW = "1"
WATER_LEVEL_RED = "2"
WATER_LEVEL_OK = "3"
WATER_LEVEL_OVERFLOW = "4"

ATTR_HUMIDITY = "humidity"
ATTR_WATER_LEVEL = "water_level"
ATTR_FAN_SPEED = "fan_speed"
ATTR_FAN_2_SPEED = "fan_2_speed"
ATTR_TIMER_TIME = "timer_time"
ATTR_OPERATION_TIME = "operation_time"
ATTR_DISC_ION_TIME = "disc_ion_time"
ATTR_DISC_ION_TIME_TO_REPLACE = "disc_ion_time_to_replace"
ATTR_DISC_ION_ERROR = "disc_ion_error"
ATTR_CHILD_LOCK = "child_lock"
ATTR_CLEANING_TIME = "cleaning_time"
ATTR_CLEANING_ERROR = "cleaning_error"
ATTR_REMAINING_CLEANING_TIME = "remaining_cleaning_time"
ATTR_TIME_TO_CLEAN = "time_to_clean"
ATTR_UVC_LAMP_ON_TIME = "uvc_lap_on_time"
ATTR_UVC_LAMP_OFF_TIME = "uvc_lap_off_time"
ATTR_FILTER_TIME = "filter_time"
ATTR_FILTER_TIME_TO_CLEAN = "filter_time_to_clean"
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
ATTR_TOLUENE = "toluene"
ATTR_NEEDS_REFILL = "needs_refill"
ATTR_NEEDS_REFILL_SOON = "needs_refill_soon"
ATTR_NEEDS_SERVICE = "needs_service"
ATTR_NEEDS_DISC_REPLACEMENT = "needs_disc_replacement"
ATTR_NEEDS_CLEANING = "needs_cleaning"
ATTR_NEEDS_FILTER_CLEANING = "needs_filter_cleaning"
ATTR_NEEDS_WATER_INLET_CHECK = "needs_water_inlet_check"
ATTR_CLEAN_MODE = "clean_mode"
ATTR_DOOR_OPEN = "door_open"
ATTR_BOX_OPEN = "box_open"
ATTR_FAN_BLOCKED = "fan_blocked"

ATTR_LED_STRIP = "led_strip"
ATTR_LED_STRIP_MODE = "led_strip_mode"
ATTR_SLEEP_MODE = "sleep_mode"

ION_DISC_REPLACE_TIME_DAYS = 121  # max seen value 17426 ~ 121 days
CLEAN_TIME_DAYS = 182  # max seen value 26210 ~ 182 days
SERVICE_TIME_DAYS = 14  # max seen value 2018 ~ 14 days
FILTER_TIME_DAYS = 182  # max seen value 26210 ~ 182 days

ONE_MINUTE_RESOLUTION = 1
FIVE_MINUTES_RESOLUTION = 5
TEN_MINUTES_RESOLUTION = 10

LED_STRIP_MODES = {
    0: "internal",
    2: "internal - no water",
    1: "external",
    3: "external - no water",
}
LED_STRIP_MODES_KEYS = list(LED_STRIP_MODES.keys())
LED_STRIP_MODES_VALUES = list(LED_STRIP_MODES.values())
