from enum import Enum, auto
import json

class DisplayMethod(Enum):
    STACK = auto()
    BLEND = auto()

class RecorderConfig():
    """
    レコーダの設定(主にjsonで出力する用途)
    """
    def __init__(self, width: int, height: int, time_sec: float, frequency: int, display: DisplayMethod, intrinsics_color = None, intrinsics_depth = None) -> None:
        self.width: int = width
        self.height: int = height
        self.time_sec: float = time_sec
        self.frequency: int = frequency
        self.display = display
        self.time_str: str = None
        self.depth_file: str = None
        self.color_file: str = None
        self.intrinsics_color = intrinsics_color
        self.intrinsics_depth = intrinsics_depth

    def toJson(self) -> str :
        encoded = json.dumps({
            "width": self.width,
            "height": self.height,
            "time_sec": self.time_sec,
            "frequency": self.frequency,
            "time": self.time_str,
            "depth_file": self.depth_file,
            "color_file": self.color_file,
            "intrinsics_color": self.intrinsics_color if isinstance(self.intrinsics_color, dict) else {
                "fx": self.intrinsics_color.fx,
                "fy": self.intrinsics_color.fy,
                "ppx": self.intrinsics_color.ppx,
                "ppy": self.intrinsics_color.ppy,
                "width": self.intrinsics_color.width,
                "height": self.intrinsics_color.height,
                "model": str(self.intrinsics_color.model),
                "coeffs": self.intrinsics_color.coeffs
            },
            "intrinsics_depth": self.intrinsics_depth if isinstance(self.intrinsics_depth, dict) else {
                "fx": self.intrinsics_depth.fx,
                "fy": self.intrinsics_depth.fy,
                "ppx": self.intrinsics_depth.ppx,
                "ppy": self.intrinsics_depth.ppy,
                "width": self.intrinsics_depth.width,
                "height": self.intrinsics_depth.height,
                "model": str(self.intrinsics_depth.model),
                "coeffs": self.intrinsics_depth.coeffs
            }
        }, sort_keys=True, indent=2)
        return encoded

    @classmethod
    def fromJson(cls, decoded: dict):
        return cls(
            width=decoded["width"],
            height=decoded["height"],
            time_sec=decoded["time_sec"],
            frequency=decoded["frequency"],
            display=None,
            intrinsics_color= decoded.get("intrinsics_color"),
            intrinsics_depth= decoded.get("intrinsics_depth")
        )