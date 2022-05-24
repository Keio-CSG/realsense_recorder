from enum import Enum, auto
import json

class DisplayMethod(Enum):
    STACK = auto()
    BLEND = auto()

class RecorderConfig():
    """
    レコーダの設定(主にjsonで出力する用途)
    """
    def __init__(self, width: int, height: int, time_sec: float, frequency: int, display: DisplayMethod) -> None:
        self.width: int = width
        self.height: int = height
        self.time_sec: float = time_sec
        self.frequency: int = frequency
        self.display = display
        self.time_str: str = None
        self.depth_file: str = None
        self.color_file: str = None

    def toJson(self) -> str :
        encoded = json.dumps({
            "width": self.width,
            "height": self.height,
            "time_sec": self.time_sec,
            "frequency": self.frequency,
            "time": self.time_str,
            "depth_file": self.depth_file,
            "color_file": self.color_file
        }, sort_keys=True, indent=2)
        return encoded

    @classmethod
    def fromJson(cls, decoded: dict):
        return cls(
            width=decoded["width"],
            height=decoded["height"],
            time_sec=decoded["time_sec"],
            frequency=decoded["frequency"],
            display=None
        )