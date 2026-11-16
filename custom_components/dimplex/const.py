"""Constants for the Dimplex integration."""
from typing import Final

DOMAIN: Final = "dimplex"

# OAuth2 Configuration
OAUTH2_AUTHORIZE_URL: Final = "https://gdtsb2c.b2clogin.com/gdtsb2c.onmicrosoft.com/B2C_1_signinsignupext/oauth2/v2.0/authorize"
OAUTH2_TOKEN_URL: Final = "https://gdtsb2c.b2clogin.com/gdtsb2c.onmicrosoft.com/B2C_1_signinsignupext/oauth2/v2.0/token"
OAUTH2_CLIENT_ID: Final = "88e2acca-0feb-4479-9b22-daba08172c94"
OAUTH2_REDIRECT_URI: Final = "http://127.0.0.1:61337/"
OAUTH2_SCOPE: Final = f"{OAUTH2_CLIENT_ID} offline_access"

# API Configuration
API_BASE_URL: Final = "https://prod.homecloud.dimplex.de/api/v1"
API_USER_AGENT: Final = "QtOAuth/1.0 (+https://www.qt.io)"

# Polling interval in seconds
DEFAULT_SCAN_INTERVAL: Final = 60

# Bypass toggle behavior: writing 1 to 2212i edge-triggers a toggle of the
# bypass state (2214i). The flag must be reset to 0 afterwards so the next
# write of 1 is detected as a fresh trigger. Since the request travels via
# the Dimplex cloud, the state change is not immediate.
BYPASS_TOGGLE_POLL_INTERVAL: Final = 2  # seconds between status reads
BYPASS_TOGGLE_TIMEOUT: Final = 60  # max seconds to wait for state to flip

# Configuration keys
CONF_DEVICE_ID: Final = "device_id"
CONF_ACCESS_TOKEN: Final = "access_token"
CONF_REFRESH_TOKEN: Final = "refresh_token"

# Variable IDs
class VarID:
    """Variable IDs for Dimplex API."""
    # Bypass & Ventilation Control (writable)
    VENTILATION_BYPASS_SWITCH: Final = "2212i"
    VENTILATION_MODE: Final = "2208i"
    
    # Temperature readings
    TEMP_WARMWATER: Final = "1305a"
    TEMP_RETURN: Final = "1294a"
    TEMP_SUPPLY: Final = "1300a"
    TEMP_HK: Final = "500a"
    TEMP_HK_SOLL: Final = "1620i"
    TEMP_HK_IST: Final = "1621i"
    TEMP_SYSTEM_SOLL: Final = "1574i"
    TEMP_SYSTEM_IST: Final = "1575i"
    TEMP_ROOM_SOLL: Final = "502a"
    TEMP_ROOM_IST: Final = "1209i"
    TEMP_DEWPOINT: Final = "1653i"
    
    # Ventilation temperatures
    VENT_TEMP_OUTSIDE: Final = "2225a"
    VENT_TEMP_SUPPLY: Final = "2226a"
    VENT_TEMP_EXHAUST: Final = "2227a"
    VENT_TEMP_OUTGOING: Final = "2228a"
    
    # Ventilation readings
    VENT_HUMIDITY_EXHAUST: Final = "2539i"
    VENT_HUMIDITY_OUTSIDE: Final = "2540i"
    VENT_VOC_EXHAUST: Final = "2543i"
    VENT_VOC_OUTSIDE: Final = "2542i"
    VENT_BYPASS_STATUS: Final = "2214i"
    VENT_FILTER_DAYS: Final = "2219i"
    VENT_EXHAUST_FLOW: Final = "2242i"
    VENT_SUPPLY_FLOW: Final = "2256i"
    VENT_SUPPLY_FAN_SPEED: Final = "2243i"
    VENT_EXHAUST_FAN_SPEED: Final = "2229i"
    
    # Compressor stats
    COMPRESSOR_RUNTIME: Final = "1617i"
    COMPRESSOR_CLOCKS_TOTAL: Final = "1491i"
    COMPRESSOR_CLOCKS_HEATING: Final = "1492i"
    COMPRESSOR_CLOCKS_HOTWATER: Final = "1493i"
    COMPRESSOR_CLOCKS_COOLING: Final = "1495i"
    
    # Climate control (room-regulated heating circuit 1)
    # 502a is the base room setpoint (a plain degC float). Note 1629i is the
    # EFFECTIVE setpoint = 502a + room-regulation raise (816i), so it reads
    # higher and must not be used as the writable setpoint.
    ROOM_SETPOINT_HK1: Final = "502a"
    ROOM_TEMP_HK1: Final = "1632i"  # Hk1_Raum_Temp - actual room temperature (x0.1)
    OPERATING_MODE: Final = "714i"  # BA_aktiv - persistent operating mode (Betriebsart)

    # Heat/energy meters (thermal kWh). Each counter is split across a low word
    # (0-9999) and a high word (x10000 steps): value = high * 10000 + low.
    HEAT_TOTAL_LOW: Final = "1660i"        # heat pump total (heating + hot water)
    HEAT_TOTAL_HIGH: Final = "1661i"
    HEAT_HEATING_LOW: Final = "1663i"      # heating
    HEAT_HEATING_HIGH: Final = "1664i"
    HEAT_HOTWATER_LOW: Final = "1669i"     # hot water
    HEAT_HOTWATER_HIGH: Final = "1670i"
    ENV_ENERGY_LOW: Final = "1644i"        # environmental (ambient) energy
    ENV_ENERGY_HIGH: Final = "1645i"
    # Resettable counterparts of the above
    HEAT_TOTAL_RES_LOW: Final = "1672i"
    HEAT_TOTAL_RES_HIGH: Final = "1673i"
    HEAT_HEATING_RES_LOW: Final = "1675i"
    HEAT_HEATING_RES_HIGH: Final = "1676i"
    HEAT_HOTWATER_RES_LOW: Final = "1681i"
    HEAT_HOTWATER_RES_HIGH: Final = "1682i"
    ENV_ENERGY_RES_LOW: Final = "1647i"
    ENV_ENERGY_RES_HIGH: Final = "1648i"

    # Status
    SMARTGRID: Final = "1246d"
    WP_STATUS_1: Final = "1586i"
    WP_STATUS_2: Final = "1500d"
    COMPRESSOR_SPEED: Final = "1472i"
    # Variables addressed by name (the cloud accepts names in "variableIds")
    WP_BLOCK_REASON: Final = "Sperr_Wp_Wert"
    WP_FAULT: Final = "Stoerung_Wert"


# All variable IDs for bulk reading
ALL_VARIABLE_IDS: Final = [
    VarID.VENTILATION_BYPASS_SWITCH,
    VarID.VENTILATION_MODE,
    VarID.TEMP_WARMWATER,
    VarID.TEMP_RETURN,
    VarID.TEMP_SUPPLY,
    VarID.TEMP_HK,
    VarID.TEMP_HK_SOLL,
    VarID.TEMP_HK_IST,
    VarID.TEMP_SYSTEM_SOLL,
    VarID.TEMP_SYSTEM_IST,
    VarID.TEMP_ROOM_SOLL,
    VarID.TEMP_ROOM_IST,
    VarID.TEMP_DEWPOINT,
    VarID.VENT_TEMP_OUTSIDE,
    VarID.VENT_TEMP_SUPPLY,
    VarID.VENT_TEMP_EXHAUST,
    VarID.VENT_TEMP_OUTGOING,
    VarID.VENT_HUMIDITY_EXHAUST,
    VarID.VENT_HUMIDITY_OUTSIDE,
    VarID.VENT_VOC_EXHAUST,
    VarID.VENT_VOC_OUTSIDE,
    VarID.VENT_BYPASS_STATUS,
    VarID.VENT_FILTER_DAYS,
    VarID.VENT_EXHAUST_FLOW,
    VarID.VENT_SUPPLY_FLOW,
    VarID.VENT_SUPPLY_FAN_SPEED,
    VarID.VENT_EXHAUST_FAN_SPEED,
    VarID.COMPRESSOR_RUNTIME,
    VarID.COMPRESSOR_CLOCKS_TOTAL,
    VarID.COMPRESSOR_CLOCKS_HEATING,
    VarID.COMPRESSOR_CLOCKS_HOTWATER,
    VarID.COMPRESSOR_CLOCKS_COOLING,
    VarID.SMARTGRID,
    VarID.WP_STATUS_1,
    VarID.WP_STATUS_2,
    VarID.COMPRESSOR_SPEED,
    VarID.ROOM_TEMP_HK1,
    VarID.OPERATING_MODE,
    VarID.WP_BLOCK_REASON,
    VarID.WP_FAULT,
    VarID.HEAT_TOTAL_LOW,
    VarID.HEAT_TOTAL_HIGH,
    VarID.HEAT_HEATING_LOW,
    VarID.HEAT_HEATING_HIGH,
    VarID.HEAT_HOTWATER_LOW,
    VarID.HEAT_HOTWATER_HIGH,
    VarID.ENV_ENERGY_LOW,
    VarID.ENV_ENERGY_HIGH,
    VarID.HEAT_TOTAL_RES_LOW,
    VarID.HEAT_TOTAL_RES_HIGH,
    VarID.HEAT_HEATING_RES_LOW,
    VarID.HEAT_HEATING_RES_HIGH,
    VarID.HEAT_HOTWATER_RES_LOW,
    VarID.HEAT_HOTWATER_RES_HIGH,
    VarID.ENV_ENERGY_RES_LOW,
    VarID.ENV_ENERGY_RES_HIGH,
]

# Status mappings
# Raw value = cloud value * 10 (e.g. 10 -> 1.0 -> Defrost). Source: Dimplex Home Cloud
# /wpm/status_value_translation (Status_Wert). Existing texts are kept for compatibility.
WP_STATUS_1_MAP: Final = {
    "0": "Off",
    "1": "Off",
    "2": "Floor Heating",
    "3": "Swimming pool",
    "4": "Hot Water",
    "5": "Cooling",
    "6": "Energy opt.",
    "10": "Defrost",
    "11": "Flow rate monitoring",
    "12": "Waiting time",
    "24": "Delay operating mode switching",
    "30": "Block",
}

WP_STATUS_2_MAP: Final = {
    "0": "Off",
    "1": "Active",
}

# Operating mode (Betriebsart, 714i) - the persistent operating mode.
# Distinct from WP_STATUS_1 (1586i), which is the current live status.
OPERATING_MODE_MAP: Final = {
    "0": "Sommer (nur Warmwasser)",
    "1": "Winter",
    "2": "Urlaub",
    "3": "Party",
    "4": "2. Wärmeerzeuger",
    "5": "Kühlen",
    "6": "Auto",
}

# Reverse mapping for setting the operating mode
OPERATING_MODE_TO_VALUE: Final = {v: k for k, v in OPERATING_MODE_MAP.items()}

VENTILATION_MODE_MAP: Final = {
    "0": "Off",
    "1": "Auto",
    "2": "Level 1",
    "3": "Level 2",
    "4": "Level 3",
}

# Reverse mapping for setting ventilation mode
VENTILATION_MODE_TO_VALUE: Final = {v: k for k, v in VENTILATION_MODE_MAP.items()}

# Block reason (Sperr_Wp_Wert). Raw value = cloud value * 10 (15 -> 1.5 -> Utility block).
WP_BLOCK_REASON_MAP: Final = {
    "0": "No block",
    "1": "p0 monitoring",
    "2": "Volume flow",
    "3": "heat pump",
    "5": "Function control",
    "7": "System control",
    "8": "Delay",
    "9": "Pump flow",
    "10": "Minimum pause time",
    "11": "Line load",
    "12": "Switch cycle block",
    "13": "Domestic hot water reheating",
    "14": "Renewable",
    "15": "Utility block",
    "16": "Soft starter",
    "17": "Flow",
    "18": "2nd heat generator",
    "19": "High pressure",
    "20": "Low pressure",
    "21": "Operating limit",
    "22": "4 way valve",
    "23": "System limit",
    "24": "Load primary circuit",
    "25": "Block external",
    "26": "Communication fault",
    "27": "Startup curcuit",
    "29": "Inverter block",
    "30": "Max. Block",
    "31": "Warm up",
    "32": "Max. operating mode switches",
    "33": "EVD Init.",
    "34": "2nd heat generator",
    "35": "Fault",
    "38": "Master communication HP",
    "39": "Master fault HP",
    "51": "Heat source min.",
    "52": "Heat source Max.",
    "53": "Return min.",
    "54": "Return Max.",
    "55": "Lead time min.",
    "56": "Flow Max.",
    "57": "Propane sensor communication",
}

# Fault code (Stoerung_Wert). Only "no fault" is known; unknown codes fall back
# to the raw number (see coordinator.get_mapped_value).
WP_FAULT_MAP: Final = {
    "0": "No fault",
}
