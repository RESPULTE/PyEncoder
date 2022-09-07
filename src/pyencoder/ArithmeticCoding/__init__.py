from pyencoder import Config


class Settings:
    PRECISION = Config["ArithmeticCoding"]["PRECISION"]

    FULL_RANGE = 1 << PRECISION
    HALF_RANGE = FULL_RANGE >> 1
    QUARTER_RANGE = HALF_RANGE >> 1
    THREE_QUARTER_RANGE = HALF_RANGE + QUARTER_RANGE

    FULL_RANGE_BITMASK = FULL_RANGE - 1

    def __setattr__(self, __name: str, __value: int) -> None:
        if __name != "PRECISION":
            raise Exception("cannot alter const")

        setattr(self, __name, __value)

        self._recalibrate()

    def _recalibrate(self) -> None:
        self.FULL_RANGE = 1 << self.PRECISION
        self.HALF_RANGE = self.FULL_RANGE >> 1
        self.QUARTER_RANGE = self.HALF_RANGE >> 1
        self.THREE_QUARTER_RANGE = self.HALF_RANGE + self.QUARTER_RANGE
        self.FULL_RANGE_BITMASK = self.FULL_RANGE - 1
