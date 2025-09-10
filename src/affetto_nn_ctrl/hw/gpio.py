from __future__ import annotations

import time
try:
    import gpiod  # type: ignore
    from gpiod.line import Direction, Value  # type: ignore
except Exception:  # noqa: BLE001
    gpiod = None  # type: ignore
    Direction = Value = None  # type: ignore

class CsLine:
    """Chip-select abstraction using libgpiod v2 request_lines API.

    Active state drives the electrical level that asserts the device CS.
    When active_high=False, the line is configured as active-low so that
    Value.ACTIVE outputs a low level.
    """
    def __init__(self, pin: int, chip: str = "/dev/gpiochip0", *, active_high: bool = True):
        if gpiod is None:
            raise RuntimeError("libgpiod not available")
        self.pin = pin
        self._chip = gpiod.Chip(chip)
        ls = gpiod.LineSettings()
        if Direction is not None:
            ls.direction = Direction.OUTPUT
        # Configure active_low mapping if available
        try:
            ls.active_low = not active_high  # type: ignore[attr-defined]
        except Exception:
            pass
        # Default to inactive state
        if Value is not None:
            ls.output_value = Value.INACTIVE
        self._req = self._chip.request_lines(consumer="cs", config={pin: ls})
        # Ensure inactive
        self.set_inactive()

    def set_active(self) -> None:
        try:
            with open("/tmp/hw_debug.log", "a") as f:
                f.write(f"[CsLine] set_active pin={self.pin}\n")
        except Exception:
            pass
        if Value is not None:
            self._req.set_values({self.pin: Value.ACTIVE})
        else:  # pragma: no cover
            self._req.set_values({self.pin: 1})  # type: ignore[arg-type]

    def set_inactive(self) -> None:
        try:
            with open("/tmp/hw_debug.log", "a") as f:
                f.write(f"[CsLine] set_inactive pin={self.pin}\n")
        except Exception:
            pass
        if Value is not None:
            self._req.set_values({self.pin: Value.INACTIVE})
        else:  # pragma: no cover
            self._req.set_values({self.pin: 0})  # type: ignore[arg-type]

    def pulse(self, dt: float = 1e-6) -> None:
        self.set_active(); time.sleep(dt); self.set_inactive()

    def set(self, val: int) -> None:
        if val:
            self.set_active()
        else:
            self.set_inactive()

    def close(self) -> None:
        try:
            self.set_inactive()
        except Exception:  # noqa: BLE001
            pass
        try:
            self._req.release()
        except Exception:  # noqa: BLE001
            pass
        try:
            self._chip.close()
        except Exception:  # noqa: BLE001
            pass

__all__ = ["CsLine"]
