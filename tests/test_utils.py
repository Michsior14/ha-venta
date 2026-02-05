"""Tests for the Venta utils module."""

from __future__ import annotations

import asyncio

from homeassistant.const import UnitOfTemperature

from custom_components.venta.utils import (
    get_from_list,
    needs_maintenance,
    retry_on_timeout,
    skip_zeros,
    venta_temperature_unit,
    venta_time_to_days_left,
    venta_time_to_minutes,
)


class TestSkipZeros:
    """Tests for skip_zeros function."""

    def test_skip_zeros_with_zero(self) -> None:
        """Test that zero values return None."""
        assert skip_zeros(0) is None

    def test_skip_zeros_with_none(self) -> None:
        """Test that None values return None."""
        assert skip_zeros(None) is None

    def test_skip_zeros_with_non_zero_int(self) -> None:
        """Test that non-zero integers are returned."""
        assert skip_zeros(42) == 42  # noqa: PLR2004
        assert skip_zeros(-1) == -1

    def test_skip_zeros_with_string(self) -> None:
        """Test that string values are returned."""
        assert skip_zeros("test") == "test"
        assert skip_zeros("") == ""

    def test_skip_zeros_with_bool(self) -> None:
        """Test that boolean values are returned correctly."""
        assert skip_zeros(True) is True
        # Note: False == 0 in Python, so it returns None
        assert skip_zeros(False) is None


class TestVentaTimeToMinutes:
    """Tests for venta_time_to_minutes function."""

    def test_with_none(self) -> None:
        """Test that None returns None."""
        assert venta_time_to_minutes(None, 1) is None
        assert venta_time_to_minutes(None, 5) is None

    def test_with_one_minute_resolution(self) -> None:
        """Test conversion with 1 minute resolution."""
        assert venta_time_to_minutes(60, 1) == 60  # noqa: PLR2004
        assert venta_time_to_minutes(0, 1) == 0

    def test_with_five_minute_resolution(self) -> None:
        """Test conversion with 5 minute resolution."""
        assert venta_time_to_minutes(12, 5) == 60  # noqa: PLR2004
        assert venta_time_to_minutes(24, 5) == 120  # noqa: PLR2004

    def test_with_ten_minute_resolution(self) -> None:
        """Test conversion with 10 minute resolution."""
        assert venta_time_to_minutes(6, 10) == 60  # noqa: PLR2004
        assert venta_time_to_minutes(12, 10) == 120  # noqa: PLR2004


class TestVentaTimeToDaysLeft:
    """Tests for venta_time_to_days_left function."""

    def test_with_none(self) -> None:
        """Test that None returns None."""
        assert venta_time_to_days_left(None, 182, 10) is None

    def test_fresh_filter(self) -> None:
        """Test calculation with a fresh filter."""
        # 0 time used = full days left
        assert venta_time_to_days_left(0, 182, 10) == 182  # noqa: PLR2004

    def test_half_used_filter(self) -> None:
        """Test calculation with half-used filter."""
        # resolution=10 means 6 ticks per hour, 144 ticks per day
        # 182 days max, half = ~91 days left
        half_used = 144 * 91  # 91 days worth of ticks
        result = venta_time_to_days_left(half_used, 182, 10)
        assert result == 91  # noqa: PLR2004

    def test_fully_used_filter(self) -> None:
        """Test calculation when filter is fully used."""
        # 182 days * 144 ticks/day = 26208 ticks
        fully_used = 144 * 182
        result = venta_time_to_days_left(fully_used, 182, 10)
        assert result == 0


class TestNeedsMaintenance:
    """Tests for needs_maintenance function."""

    def test_with_none(self) -> None:
        """Test that None returns None."""
        assert needs_maintenance(None, 182, 10) is None

    def test_no_maintenance_needed(self) -> None:
        """Test when maintenance is not needed."""
        assert needs_maintenance(0, 182, 10) is False

    def test_maintenance_needed(self) -> None:
        """Test when maintenance is needed (days left <= 0)."""
        # More than 182 days worth of ticks
        fully_used = 144 * 183
        assert needs_maintenance(fully_used, 182, 10) is True


class TestGetFromList:
    """Tests for get_from_list function."""

    def test_with_none_list(self) -> None:
        """Test that None list returns default."""
        assert get_from_list(None, 0) is None
        assert get_from_list(None, 0, "default") == "default"

    def test_valid_index(self) -> None:
        """Test getting valid index."""
        test_list = ["a", "b", "c"]
        assert get_from_list(test_list, 0) == "a"
        assert get_from_list(test_list, 2) == "c"

    def test_invalid_index(self) -> None:
        """Test that invalid index returns default."""
        test_list = ["a", "b", "c"]
        assert get_from_list(test_list, 10) is None
        assert get_from_list(test_list, 10, "fallback") == "fallback"

    def test_negative_index(self) -> None:
        """Test negative indexing works."""
        test_list = ["a", "b", "c"]
        assert get_from_list(test_list, -1) == "c"


class TestVentaTemperatureUnit:
    """Tests for venta_temperature_unit function."""

    def test_with_none(self) -> None:
        """Test that None returns None."""
        assert venta_temperature_unit(None) is None

    def test_celsius(self) -> None:
        """Test that 0 returns Celsius."""
        assert venta_temperature_unit(0) == UnitOfTemperature.CELSIUS

    def test_fahrenheit(self) -> None:
        """Test that non-zero returns Fahrenheit."""
        assert venta_temperature_unit(1) == UnitOfTemperature.FAHRENHEIT
        assert venta_temperature_unit(2) == UnitOfTemperature.FAHRENHEIT


class TestRetryOnTimeout:
    """Tests for retry_on_timeout decorator."""

    async def test_successful_call(self) -> None:
        """Test that successful calls return immediately."""
        call_count = 0

        @retry_on_timeout(retries=3, timeout=1, delay=0.1)
        async def successful_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_func()
        assert result == "success"
        assert call_count == 1

    async def test_retry_on_timeout_exhausted(self) -> None:
        """Test that retries are exhausted on continuous timeouts."""
        call_count = 0

        @retry_on_timeout(retries=3, timeout=0.01, delay=0.01)
        async def always_timeout() -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(1)  # Will always timeout
            return "never"

        result = await always_timeout()
        assert result is None
        assert call_count == 3  # noqa: PLR2004

    async def test_retry_succeeds_eventually(self) -> None:
        """Test that function succeeds after initial failures."""
        call_count = 0

        @retry_on_timeout(retries=5, timeout=0.5, delay=0.01)
        async def succeed_on_third() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # noqa: PLR2004
                await asyncio.sleep(1)  # Timeout on first two calls
            return "success"

        result = await succeed_on_third()
        assert result == "success"
        assert call_count == 3  # noqa: PLR2004
