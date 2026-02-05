"""Tests for the Venta JSON utilities module."""

from __future__ import annotations

from custom_components.venta.json import _RawJSONDecoder, extract_json


class TestExtractJson:
    """Tests for extract_json function."""

    def test_single_json_object(self) -> None:
        """Test extracting a single JSON object."""
        result = list(extract_json('{"key": "value"}'))
        assert len(result) == 1
        assert result[0] == {"key": "value"}

    def test_json_with_prefix(self) -> None:
        """Test extracting JSON with text prefix."""
        result = list(extract_json('HTTP/1.1 200 OK\n{"data": 123}'))
        assert len(result) == 1
        assert result[0] == {"data": 123}

    def test_json_with_suffix(self) -> None:
        """Test extracting JSON with text suffix."""
        result = list(extract_json('{"data": 123} some text after'))
        assert len(result) == 1
        assert result[0] == {"data": 123}

    def test_multiple_json_objects(self) -> None:
        """Test extracting multiple JSON objects."""
        result = list(extract_json('{"first": 1} {"second": 2}'))
        assert len(result) == 2
        assert result[0] == {"first": 1}
        assert result[1] == {"second": 2}

    def test_nested_json(self) -> None:
        """Test extracting nested JSON objects."""
        result = list(extract_json('{"outer": {"inner": "value"}}'))
        assert len(result) == 1
        assert result[0] == {"outer": {"inner": "value"}}

    def test_empty_string(self) -> None:
        """Test extracting from empty string."""
        result = list(extract_json(""))
        assert len(result) == 0

    def test_no_json(self) -> None:
        """Test extracting from string with no JSON."""
        result = list(extract_json("plain text without json"))
        assert len(result) == 0

    def test_malformed_json(self) -> None:
        """Test handling malformed JSON gracefully."""
        # Should skip malformed and find valid JSON
        result = list(extract_json('{"incomplete {"valid": true}'))
        assert len(result) == 1
        assert result[0] == {"valid": True}

    def test_json_with_array(self) -> None:
        """Test extracting JSON with arrays."""
        result = list(extract_json('{"items": [1, 2, 3]}'))
        assert len(result) == 1
        assert result[0] == {"items": [1, 2, 3]}

    def test_complex_venta_response(self) -> None:
        """Test extracting a typical Venta device response."""
        venta_response = """HTTP/1.1 200 OK
Content-Type: application/json

{"Header": {"MacAdress": "00:11:22:33:44:55", "DeviceType": 1}, "Action": {"Power": true, "FanSpeed": 3}, "Measure": {"Temperature": 22.5}}"""
        result = list(extract_json(venta_response))
        assert len(result) == 1
        assert result[0]["Header"]["MacAdress"] == "00:11:22:33:44:55"
        assert result[0]["Action"]["Power"] is True
        assert result[0]["Measure"]["Temperature"] == 22.5

    def test_index_parameter(self) -> None:
        """Test starting extraction from specific index."""
        result = list(extract_json('{"skip": 1} {"include": 2}', index=10))
        assert len(result) == 1
        assert result[0] == {"include": 2}

    def test_json_boolean_values(self) -> None:
        """Test handling JSON boolean values."""
        result = list(extract_json('{"enabled": true, "disabled": false}'))
        assert len(result) == 1
        assert result[0]["enabled"] is True
        assert result[0]["disabled"] is False

    def test_json_null_values(self) -> None:
        """Test handling JSON null values."""
        result = list(extract_json('{"value": null}'))
        assert len(result) == 1
        assert result[0]["value"] is None


class TestRawJSONDecoder:
    """Tests for _RawJSONDecoder class."""

    def test_basic_decode(self) -> None:
        """Test basic JSON decoding."""
        decoder = _RawJSONDecoder()
        result = decoder.decode('{"key": "value"}')
        assert result == {"key": "value"}

    def test_decode_with_index(self) -> None:
        """Test decoding from specific index."""
        decoder = _RawJSONDecoder(index=5)
        result = decoder.decode('xxxxx{"key": "value"}')
        assert result == {"key": "value"}

    def test_end_hook_called(self) -> None:
        """Test that end_hook is called with correct position."""
        end_position = None

        def capture_end(end: int) -> None:
            nonlocal end_position
            end_position = end

        decoder = _RawJSONDecoder(end_hook=capture_end)
        decoder.decode('{"key": "value"} extra')
        assert end_position == 16

    def test_decode_partial_string(self) -> None:
        """Test that decoder stops at first complete JSON object."""
        decoder = _RawJSONDecoder()
        result = decoder.decode('{"first": 1} {"second": 2}')
        assert result == {"first": 1}
