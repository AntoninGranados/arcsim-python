from pathlib import Path
from typing import Optional, Any

import json
import tempfile

# TODO use `@dataclass` decorator instead of this custom ConfigTemplate class
class ConfigTemplate:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def dict(self):
        self_dict = {}
        for k, v in self.__dict__.items():
            if type(v).__base__ == ConfigTemplate:
                self_dict[k] = v.dict()
            elif type(v) == list or type(v) == tuple:
                self_dict[k] = []
                for e in v:
                    if type(e).__base__ == ConfigTemplate:
                        self_dict[k].append(e.dict())
                    else:
                        self_dict[k].append(e)
            else:
                self_dict[k] = v
        return self_dict
    
class Vec3(ConfigTemplate):
    x: float
    y: float
    z: float

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

    def dict(self): return [self.x, self.y, self.z]

    
class Rotation(ConfigTemplate):
    angle: float
    axis: Vec3

    def dict(self): return [self.angle, *self.axis.dict()]

class Transform(ConfigTemplate):
    translate: Optional[Vec3]
    rotate: Optional[Rotation]

class Material(ConfigTemplate):
    data: Path
    thicken: float
    strain_limits: tuple[float, float]

class Remesh(ConfigTemplate):
    refine_angle: float
    refine_compression: float
    refine_velocity: float
    size: tuple[float, float]
    aspect_min: float

class Cloth(ConfigTemplate):
    mesh: Path
    transform: Optional[Transform]
    remesh: Optional[Remesh]
    materials: list[Material]

class Handle(ConfigTemplate):
    nodes: list[int]

class Wind(ConfigTemplate):
    velocity: Vec3
    density: float
    drag: float

class Magic(ConfigTemplate):
    repulsion_thickness: float = 10e-3
    collision_stiffness: float = 1e6

class Config(ConfigTemplate):
    frame_time: float
    frame_steps: int
    end_time: float

    cloths: list[Cloth] = []

    gravity: Optional[Vec3] = Vec3(9.81, 0, 0)
    handles: Optional[list[Handle]]
    wind: Optional[Wind]
    magic: Magic

    disable: Optional[list[str]]

    def upload(self) -> Path:
        """
        Create a temporary file containing the formated config in a `.json` file
        
        ! Don't forget to clean the file afer using `config.cleanup(path)` with the path provided by this function
        """

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w')
        json.dump(self.dict(), tmp, indent=4)
        tmp.close()
        return Path(tmp.name)     # tempfile path

    def cleanup(self, config_file: Path | str):
        Path(config_file).unlink()
