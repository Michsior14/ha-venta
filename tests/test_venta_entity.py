"""Tests for Venta entity classes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.humidifier import MODE_AUTO, MODE_BOOST, MODE_SLEEP

from custom_components.venta.venta import VentaData
from custom_components.venta.venta_entity import (
    VentaBinarySensor,
    VentaBinarySensorEntityDescription,
    VentaBaseHumidifierEntity,
    VentaLight,
    VentaSelect,
    VentaSelectEntityDescription,
    VentaSensor,
    VentaSensorEntityDescription,
    VentaSwitch,
    VentaSwitchEntityDescription,
    VentaV0HumidifierEntity,
    VentaV2HumidifierEntity,
    VentaV3HumidifierEntity,
)


def create_mock_coordinator(data: VentaData | None = None) -> MagicMock:
    """Create a mock coordinator for testing."""
    coordinator = MagicMock()
    coordinator.data = data or VentaData(
        header={"MacAdress": "00:11:22:33:44:55", "DeviceType": 1},
        action={"Power": True, "FanSpeed": 3, "TargetHum": 50, "Automatic": False},
        info={"Warnings": 0},
        measure={"Humidity": 45, "Temperature": 22},
    )
    coordinator.api.device.mac = "00:11:22:33:44:55"
    coordinator.api.device.action = AsyncMock()
    coordinator.device_info = {
        "identifiers": {("venta", "00:11:22:33:44:55")},
        "name": "Venta",
        "manufacturer": "Venta",
        "model": "LP60",
    }
    return coordinator


class TestVentaBinarySensor:
    """Tests for VentaBinarySensor."""

    def test_initialization(self) -> None:
        """Test binary sensor initialization."""
        coordinator = create_mock_coordinator()
        description = VentaBinarySensorEntityDescription(
            key="test_sensor",
            value_func=lambda data: data.action.get("Power"),
        )
        sensor = VentaBinarySensor(coordinator, description)

        assert sensor.entity_description == description
        assert sensor._attr_unique_id == "00:11:22:33:44:55-test_sensor"

    def test_is_on_true(self) -> None:
        """Test is_on returns True when power is on."""
        coordinator = create_mock_coordinator()
        description = VentaBinarySensorEntityDescription(
            key="power",
            value_func=lambda data: data.action.get("Power"),
        )
        sensor = VentaBinarySensor(coordinator, description)

        assert sensor.is_on is True

    def test_is_on_false(self) -> None:
        """Test is_on returns False when power is off."""
        data = VentaData(action={"Power": False})
        coordinator = create_mock_coordinator(data)
        description = VentaBinarySensorEntityDescription(
            key="power",
            value_func=lambda data: data.action.get("Power"),
        )
        sensor = VentaBinarySensor(coordinator, description)

        assert sensor.is_on is False


class TestVentaSensor:
    """Tests for VentaSensor."""

    def test_initialization(self) -> None:
        """Test sensor initialization."""
        coordinator = create_mock_coordinator()
        description = VentaSensorEntityDescription(
            key="temperature",
            value_func=lambda coord: coord.data.measure.get("Temperature"),
        )
        sensor = VentaSensor(coordinator, description)

        assert sensor.entity_description == description
        assert sensor._attr_unique_id == "00:11:22:33:44:55-temperature"

    def test_native_value(self) -> None:
        """Test native_value returns sensor value."""
        coordinator = create_mock_coordinator()
        description = VentaSensorEntityDescription(
            key="temperature",
            value_func=lambda coord: coord.data.measure.get("Temperature"),
        )
        sensor = VentaSensor(coordinator, description)

        assert sensor.native_value == 22

    def test_native_unit_of_measurement_with_unit_func(self) -> None:
        """Test unit of measurement with custom unit function."""
        coordinator = create_mock_coordinator()
        description = VentaSensorEntityDescription(
            key="temperature",
            value_func=lambda coord: coord.data.measure.get("Temperature"),
            unit_func=lambda coord: "°C",
        )
        sensor = VentaSensor(coordinator, description)

        assert sensor.native_unit_of_measurement == "°C"

    def test_native_unit_of_measurement_without_unit_func(self) -> None:
        """Test unit of measurement without custom unit function."""
        coordinator = create_mock_coordinator()
        description = VentaSensorEntityDescription(
            key="humidity",
            value_func=lambda coord: coord.data.measure.get("Humidity"),
            native_unit_of_measurement="%",
        )
        sensor = VentaSensor(coordinator, description)

        assert sensor.native_unit_of_measurement == "%"


class TestVentaSwitch:
    """Tests for VentaSwitch."""

    def test_initialization(self) -> None:
        """Test switch initialization."""
        coordinator = create_mock_coordinator()
        description = VentaSwitchEntityDescription(
            key="power",
            value_func=lambda data: data.action.get("Power"),
            action_func=lambda data, on: {"Action": {"Power": on}},
        )
        switch = VentaSwitch(coordinator, description)

        assert switch.entity_description == description
        assert switch._attr_unique_id == "00:11:22:33:44:55-power"

    def test_is_on(self) -> None:
        """Test is_on returns switch state."""
        coordinator = create_mock_coordinator()
        description = VentaSwitchEntityDescription(
            key="power",
            value_func=lambda data: data.action.get("Power"),
            action_func=lambda data, on: {"Action": {"Power": on}},
        )
        switch = VentaSwitch(coordinator, description)

        assert switch.is_on is True

    async def test_turn_on(self) -> None:
        """Test turning switch on."""
        coordinator = create_mock_coordinator()
        description = VentaSwitchEntityDescription(
            key="power",
            value_func=lambda data: data.action.get("Power"),
            action_func=lambda data, on: {"Action": {"Power": on}},
        )
        switch = VentaSwitch(coordinator, description)

        await switch.async_turn_on()
        coordinator.api.device.action.assert_called_once()

    async def test_turn_off(self) -> None:
        """Test turning switch off."""
        coordinator = create_mock_coordinator()
        description = VentaSwitchEntityDescription(
            key="power",
            value_func=lambda data: data.action.get("Power"),
            action_func=lambda data, on: {"Action": {"Power": on}},
        )
        switch = VentaSwitch(coordinator, description)

        await switch.async_turn_off()
        coordinator.api.device.action.assert_called_once()


class TestVentaSelect:
    """Tests for VentaSelect."""

    def test_initialization(self) -> None:
        """Test select initialization."""
        coordinator = create_mock_coordinator()
        description = VentaSelectEntityDescription(
            key="fan_speed",
            options=["1", "2", "3"],
            value_func=lambda data: str(data.action.get("FanSpeed")),
            action_func=lambda opt: {"Action": {"FanSpeed": int(opt)}},
        )
        select = VentaSelect(coordinator, description)

        assert select.entity_description == description
        assert select._attr_unique_id == "00:11:22:33:44:55-fan_speed"
        assert select._attr_options == ["1", "2", "3"]

    def test_current_option(self) -> None:
        """Test current_option returns selected value."""
        coordinator = create_mock_coordinator()
        description = VentaSelectEntityDescription(
            key="fan_speed",
            options=["1", "2", "3"],
            value_func=lambda data: str(data.action.get("FanSpeed")),
            action_func=lambda opt: {"Action": {"FanSpeed": int(opt)}},
        )
        select = VentaSelect(coordinator, description)

        assert select.current_option == "3"

    async def test_select_option(self) -> None:
        """Test selecting an option."""
        coordinator = create_mock_coordinator()
        description = VentaSelectEntityDescription(
            key="fan_speed",
            options=["1", "2", "3"],
            value_func=lambda data: str(data.action.get("FanSpeed")),
            action_func=lambda opt: {"Action": {"FanSpeed": int(opt)}},
        )
        select = VentaSelect(coordinator, description)

        await select.async_select_option("2")
        coordinator.api.device.action.assert_called_once()


class TestVentaLight:
    """Tests for VentaLight."""

    def test_initialization(self) -> None:
        """Test light initialization."""
        coordinator = create_mock_coordinator()
        coordinator.data.action["LEDStripActive"] = True
        coordinator.data.action["LEDStrip"] = "#FF0000"
        light = VentaLight(coordinator)

        assert light._attr_unique_id == "00:11:22:33:44:55-led_strip"

    def test_is_on(self) -> None:
        """Test is_on returns light state."""
        coordinator = create_mock_coordinator()
        coordinator.data.action["LEDStripActive"] = True
        light = VentaLight(coordinator)

        assert light.is_on is True

    def test_rgb_color(self) -> None:
        """Test rgb_color returns color value."""
        coordinator = create_mock_coordinator()
        coordinator.data.action["LEDStrip"] = "#FF0000"
        light = VentaLight(coordinator)

        assert light.rgb_color == [255, 0, 0]

    async def test_turn_on_without_color(self) -> None:
        """Test turning light on without color."""
        coordinator = create_mock_coordinator()
        light = VentaLight(coordinator)

        await light.async_turn_on()
        coordinator.api.device.action.assert_called_once_with(
            {"Action": {"LEDStripActive": True}}, coordinator
        )

    async def test_turn_on_with_color(self) -> None:
        """Test turning light on with color."""
        coordinator = create_mock_coordinator()
        light = VentaLight(coordinator)

        await light.async_turn_on(rgb_color=(0, 255, 0))
        coordinator.api.device.action.assert_called_once()
        call_args = coordinator.api.device.action.call_args[0][0]
        assert "LEDStrip" in call_args["Action"]

    async def test_turn_off(self) -> None:
        """Test turning light off."""
        coordinator = create_mock_coordinator()
        light = VentaLight(coordinator)

        await light.async_turn_off()
        coordinator.api.device.action.assert_called_once_with(
            {"Action": {"LEDStripActive": False}}, coordinator
        )


class TestVentaBaseHumidifierEntity:
    """Tests for VentaBaseHumidifierEntity."""

    def create_humidifier(
        self, data: VentaData | None = None
    ) -> VentaBaseHumidifierEntity:
        """Create a humidifier entity for testing."""
        coordinator = create_mock_coordinator(data)
        return VentaV2HumidifierEntity(
            coordinator, modes=[MODE_AUTO, MODE_SLEEP, "level_1", "level_2", "level_3"]
        )

    def test_initialization(self) -> None:
        """Test humidifier initialization."""
        humidifier = self.create_humidifier()
        assert humidifier._attr_min_humidity == 30
        assert humidifier._attr_max_humidity == 70

    def test_is_on_true(self) -> None:
        """Test is_on returns True."""
        humidifier = self.create_humidifier()
        assert humidifier.is_on is True

    def test_is_on_false(self) -> None:
        """Test is_on returns False."""
        data = VentaData(action={"Power": False})
        humidifier = self.create_humidifier(data)
        assert humidifier.is_on is False

    def test_mode_auto(self) -> None:
        """Test mode returns auto."""
        data = VentaData(action={"Automatic": True, "FanSpeed": 2})
        humidifier = self.create_humidifier(data)
        assert humidifier.mode == MODE_AUTO

    def test_mode_sleep(self) -> None:
        """Test mode returns sleep."""
        data = VentaData(action={"Automatic": False, "SleepMode": True, "FanSpeed": 1})
        humidifier = self.create_humidifier(data)
        assert humidifier.mode == MODE_SLEEP

    def test_mode_level(self) -> None:
        """Test mode returns level."""
        data = VentaData(action={"Automatic": False, "SleepMode": False, "FanSpeed": 3})
        humidifier = self.create_humidifier(data)
        assert humidifier.mode == "level_3"

    def test_target_humidity(self) -> None:
        """Test target_humidity returns value."""
        humidifier = self.create_humidifier()
        assert humidifier.target_humidity == 50

    def test_current_humidity(self) -> None:
        """Test current_humidity returns value."""
        humidifier = self.create_humidifier()
        assert humidifier.current_humidity == 45

    async def test_turn_on(self) -> None:
        """Test turning humidifier on."""
        humidifier = self.create_humidifier()
        await humidifier.async_turn_on()
        humidifier._device.action.assert_called_once()

    async def test_turn_off(self) -> None:
        """Test turning humidifier off."""
        humidifier = self.create_humidifier()
        await humidifier.async_turn_off()
        humidifier._device.action.assert_called_once()

    async def test_set_humidity(self) -> None:
        """Test setting humidity."""
        humidifier = self.create_humidifier()
        await humidifier.async_set_humidity(60)
        humidifier._device.action.assert_called_once()

    async def test_set_mode_auto(self) -> None:
        """Test setting auto mode."""
        humidifier = self.create_humidifier()
        await humidifier.async_set_mode(MODE_AUTO)
        humidifier._device.action.assert_called_once()

    async def test_set_mode_sleep(self) -> None:
        """Test setting sleep mode."""
        humidifier = self.create_humidifier()
        await humidifier.async_set_mode(MODE_SLEEP)
        humidifier._device.action.assert_called_once()

    async def test_set_mode_level(self) -> None:
        """Test setting level mode."""
        humidifier = self.create_humidifier()
        await humidifier.async_set_mode("level_2")
        humidifier._device.action.assert_called_once()

    def test_map_to_action(self) -> None:
        """Test _map_to_action wraps data."""
        humidifier = self.create_humidifier()
        result = humidifier._map_to_action({"Power": True})
        assert result == {"Action": {"Power": True}}


class TestVentaV0HumidifierEntity:
    """Tests for VentaV0HumidifierEntity."""

    def create_humidifier(self) -> VentaV0HumidifierEntity:
        """Create a V0 humidifier entity for testing."""
        coordinator = create_mock_coordinator()
        return VentaV0HumidifierEntity(
            coordinator,
            modes=[MODE_AUTO, MODE_SLEEP, MODE_BOOST, "level_1", "level_2", "level_3"],
        )

    async def test_set_mode_auto(self) -> None:
        """Test setting auto mode."""
        humidifier = self.create_humidifier()
        await humidifier.async_set_mode(MODE_AUTO)
        humidifier._device.action.assert_called_once()

    async def test_set_mode_sleep(self) -> None:
        """Test setting sleep mode."""
        humidifier = self.create_humidifier()
        await humidifier.async_set_mode(MODE_SLEEP)
        humidifier._device.action.assert_called_once()

    async def test_set_mode_boost(self) -> None:
        """Test setting boost mode."""
        humidifier = self.create_humidifier()
        await humidifier.async_set_mode(MODE_BOOST)
        humidifier._device.action.assert_called_once()

    async def test_set_mode_level(self) -> None:
        """Test setting level mode."""
        humidifier = self.create_humidifier()
        await humidifier.async_set_mode("level_3")
        humidifier._device.action.assert_called_once()


class TestVentaV3HumidifierEntity:
    """Tests for VentaV3HumidifierEntity."""

    def create_humidifier(
        self, data: VentaData | None = None
    ) -> VentaV3HumidifierEntity:
        """Create a V3 humidifier entity for testing."""
        coordinator = create_mock_coordinator(data)
        return VentaV3HumidifierEntity(
            coordinator, modes=[MODE_AUTO, MODE_SLEEP, "level_1", "level_2", "level_3"]
        )

    def test_map_to_action(self) -> None:
        """Test _map_to_action for V3 protocol."""
        humidifier = self.create_humidifier()
        result = humidifier._map_to_action({"Power": True})
        assert result == {"Power": True, "Action": "control"}

    async def test_turn_on(self) -> None:
        """Test turning V3 humidifier on."""
        data = VentaData(action={"Automatic": True, "FanSpeed": 2, "SleepMode": False})
        humidifier = self.create_humidifier(data)
        await humidifier.async_turn_on()
        humidifier._device.action.assert_called_once()

    async def test_turn_on_non_automatic(self) -> None:
        """Test turning V3 humidifier on when not in auto mode."""
        data = VentaData(action={"Automatic": False, "FanSpeed": 2, "SleepMode": True})
        humidifier = self.create_humidifier(data)
        await humidifier.async_turn_on()
        humidifier._device.action.assert_called_once()

    async def test_turn_off(self) -> None:
        """Test turning V3 humidifier off."""
        data = VentaData(action={"Automatic": False, "FanSpeed": 2, "SleepMode": False})
        humidifier = self.create_humidifier(data)
        await humidifier.async_turn_off()
        humidifier._device.action.assert_called_once()

    async def test_set_humidity(self) -> None:
        """Test setting humidity for V3."""
        data = VentaData(action={"Power": True, "Automatic": True})
        humidifier = self.create_humidifier(data)
        await humidifier.async_set_humidity(55)
        humidifier._device.action.assert_called_once()

    async def test_set_mode_auto(self) -> None:
        """Test setting auto mode for V3."""
        humidifier = self.create_humidifier()
        await humidifier.async_set_mode(MODE_AUTO)
        humidifier._device.action.assert_called_once()

    async def test_set_mode_sleep(self) -> None:
        """Test setting sleep mode for V3."""
        humidifier = self.create_humidifier()
        await humidifier.async_set_mode(MODE_SLEEP)
        humidifier._device.action.assert_called_once()

    async def test_set_mode_level(self) -> None:
        """Test setting level mode for V3."""
        data = VentaData(action={"SleepMode": False})
        humidifier = self.create_humidifier(data)
        await humidifier.async_set_mode("level_2")
        humidifier._device.action.assert_called_once()
