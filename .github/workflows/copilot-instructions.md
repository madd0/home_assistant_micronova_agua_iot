# GitHub Copilot Instructions

You are an expert Home Assistant developer assisting with the `aguaiot` custom integration.

## Core Principles
1.  **Follow Home Assistant Best Practices**: Adhere to the official developer documentation for architecture, style, and patterns.
2.  **Type Hinting**: Use strict type hinting (`typing`, `collections.abc`) as per modern Python standards.
3.  **Async First**: Prefer asynchronous methods (`async def`) and Home Assistant's async APIs (`hass.async_add_executor_job`, etc.).
4.  **Logging**: Use the module-level `_LOGGER` (from `logging.getLogger(__name__)`) for all logging.
5.  **Error Handling**: Catch specific exceptions (`UnauthorizedError`, `ConnectionError`, `AguaIOTError`) from the aguaiot API client.

## Code Style
- Use `ruff` for linting and formatting if available.
- Follow PEP 8.
- Use descriptive variable names.
- Add docstrings to modules, classes, and functions.

## Specific Integration Context

### Overview
**Integration Name**: Micronova Agua IOT  
**Domain**: `aguaiot`  
**Type**: Cloud-polling hub integration for pellet stoves and heating devices  
**Version**: 0.6.1  
**Repository**: https://github.com/vincentwolsink/home_assistant_micronova_agua_iot  
**Maintainer**: @vincentwolsink

This integration controls heating devices (primarily pellet stoves) connected via the Agua IOT platform by Micronova. It supports 30+ vendor mobile apps including MCZ, Piazzetta, Klover, Ravelli, Nobis, Alfaplam, and many others.

### Architecture

#### Entry Setup (`__init__.py`)
- Uses Home Assistant's config flow (no YAML configuration)
- Creates an `aguaiot` API client instance with credentials from config entry
- Sets up a `DataUpdateCoordinator` with 60-second update interval (`UPDATE_INTERVAL`)
- Forwards setup to all platforms: `climate`, `binary_sensor`, `sensor`, `switch`, `number`
- Stores coordinator and agua client in `hass.data[DOMAIN][entry.entry_id]`

#### API Client (`aguaiot.py`)
- Main class: `aguaiot` (note: lowercase)
- **Dependencies**: `httpx` (async HTTP), `simpleeval` (for register formula evaluation), `jwt` (token parsing)
- **Authentication**: JWT-based with token refresh mechanism
- **Key Methods**:
  - `connect()`: Registers app, logs in, fetches devices and their registers
  - `update()`: Updates all device data from cloud
  - `login()`: Authenticates and stores tokens
  - `fetch_devices()`: Gets list of user devices
  - `fetch_device_information()`: Gets register maps for each device
- **Exceptions**: `AguaIOTError` (base), `ConnectionError`, `UnauthorizedError`

#### Configuration Flow (`config_flow.py`)
- Prompts user to select from `ENDPOINTS` dictionary (30+ vendor apps)
- Each endpoint has `CONF_API_URL`, `CONF_CUSTOMER_CODE`, and optionally `CONF_LOGIN_API_URL`, `CONF_BRAND_ID`, `CONF_BRAND`
- Generates unique UUID for device identification
- Validates credentials by attempting connection
- Prevents duplicate entries (same email + API URL)

#### Constants (`const.py`)
- **ENDPOINTS**: Dictionary mapping vendor app names to their API endpoints
- **Custom Entity Descriptions**: Extended dataclasses for entity metadata
  - `AguaIOTBinarySensorEntityDescription`: Adds `force_enabled`, `hybrid_only`, `icon_on`
  - `AguaIOTSensorEntityDescription`: Adds `force_enabled`, `hybrid_only`, `hybrid_exclude`, `raw_value`
  - `AguaIOTNumberEntityDescription`: Adds `force_enabled`, `hybrid_only`, `hybrid_exclude`
  - `AguaIOTCanalizationEntityDescription`: Adds keys for temperature set/get and enable registers
- **Entity Definitions**: Tuples of entity descriptions (`BINARY_SENSORS`, `SENSORS`, `SWITCHES`, `NUMBERS`, `CLIMATE_CANALIZATIONS`)
- **Device Variants**: 
  - `AIR_VARIANTS`: `["air", "air2", "air_palm"]` - air temperature control
  - `WATER_VARIANTS`: `["water", "h2o", "h2o_mandata"]` - water temperature control
- **Status Lists**:
  - `STATUS_OFF`: States indicating device is off
  - `STATUS_IDLE`: States indicating device is idle/standby
- **Modes**: `MODE_WOOD`, `MODE_PELLETS` for hybrid devices

### Platforms

#### Climate (`climate.py`)
- **Main Device Types**:
  1. `AguaIOTAirDevice`: Primary air temperature control (all devices)
  2. `AguaIOTWaterDevice`: Water/heating circuit control (water-capable devices)
  3. `AguaIOTCanalizationDevice`: Additional ventilation zones (canalization, multifire, vents)
- **Features**:
  - Target temperature control
  - HVAC modes: `AUTO`, `HEAT`, `OFF`
  - HVAC actions derived from device status
  - Custom services: `sync_clock`, `sync_schedule`, `sync_custom_power_levels`
- **Pattern**: All climate entities inherit from `CoordinatorEntity` and `ClimateEntity`
- **Register-based**: Uses device registers (e.g., `temp_air_set`, `status_get`, `on_off_set`)

#### Sensor (`sensor.py`)
- Temperature sensors (smoke, flame, air, water)
- Status and alarm sensors (enum type)
- Operational sensors (power, RPM, pressure)
- Uses `CoordinatorEntity` + `SensorEntity`
- Filters entities based on available registers and device capabilities (hybrid vs standard)

#### Binary Sensor (`binary_sensor.py`)
- Pellet depletion
- External thermostat status
- Problem detection
- Uses `CoordinatorEntity` + `BinarySensorEntity`

#### Switch (`switch.py`)
- Natural mode, standby, auto mode, powerful mode
- Uses `CoordinatorEntity` + `SwitchEntity`
- Controls device operational modes via register writes

#### Number (`number.py`)
- Power level control (pellet/wood)
- Energy saving temperature thresholds
- Uses `CoordinatorEntity` + `NumberEntity`

### Key Patterns

1. **Entity Creation**: 
   - All entities check if corresponding registers exist on the device before creating
   - Use `device.get_register_enabled(key)` to check availability
   - Entity descriptions can specify `force_enabled`, `hybrid_only`, `hybrid_exclude`

2. **Data Coordinator**:
   - Single coordinator per config entry
   - Calls `agua.update()` every 60 seconds
   - All entities subscribe to coordinator updates

3. **Device Registers**:
   - Devices have a `registers` dict with keys like `temp_air_set`, `status_get`, etc.
   - Register values can have formulas for conversion (evaluated with `simpleeval`)
   - Write operations use `device.set_register()` which queues jobs

4. **Hybrid Devices**:
   - Support both pellet and wood fuel
   - Have duplicate registers (e.g., `power_set` for pellet, `power_wood_set` for wood)
   - Entity descriptions use `hybrid_only` or `hybrid_exclude` flags

5. **Canalization Pattern**:
   - Uses regex patterns to detect additional climate zones
   - Dynamic entity creation based on register matches
   - Each canalization gets its own climate entity

### Testing & Fixtures

The `fixtures/` directory contains JSON files with register definitions from real devices:
- `mcz.json`, `piazzetta_*.json`, `nobis_*.json`, `ravelli*.json`, etc.
- Used for testing and understanding device capabilities
- Show available registers, their types, formulas, and encoded values

### Dependencies (manifest.json)
- `httpx`: Async HTTP client
- `simpleeval`: Safe formula evaluation for register transformations
- No Home Assistant dependencies (standalone integration)

### Common Patterns to Follow

**When adding new entities:**
```python
# 1. Define in const.py with custom description
NEW_ENTITY = AguaIOTSensorEntityDescription(
    key="register_key",
    name="Display Name",
    # ... other properties
)

# 2. In platform file, check register exists
if "register_key" in device.registers:
    entities.append(NewEntity(coordinator, device))
```

**When reading device data:**
```python
# Use coordinator data
value = self.coordinator.data  # triggers update
device_value = self.device.registers["key_name"]
```

**When writing device data:**
```python
await self.device.set_register("register_key", value)
await self.coordinator.async_request_refresh()
```

### Configuration Values
- `CONF_API_URL`: Cloud endpoint URL
- `CONF_CUSTOMER_CODE`: Vendor-specific code
- `CONF_EMAIL`: User email
- `CONF_PASSWORD`: User password
- `CONF_UUID`: Generated device UUID
- `CONF_LOGIN_API_URL`: Optional alternate login endpoint (Piazzetta/MySuperior)
- `CONF_BRAND_ID`: Optional brand identifier
- `CONF_BRAND`: Optional brand name

### Important Notes
- Integration uses cloud polling (not local)
- Update interval is 60 seconds (don't change without good reason)
- Some vendors (like Piazzetta) use different login endpoints
- The `aguaiot` class name is intentionally lowercase (legacy from original py-agua-iot library)
- Always check for `UnauthorizedError` - tokens can expire
- Device registers are fetched once during setup, not on every update

## Testing
- Test with real device fixtures from `fixtures/` directory
- When suggesting changes, consider impact on all device types (air, water, canalization, hybrid)
- Verify register availability before accessing
- Test authentication flow and token refresh
- Ensure backward compatibility with existing config entries