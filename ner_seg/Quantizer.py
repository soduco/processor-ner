from enum import Enum
from typing import Any, Union, List
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt


@dataclass
class Quantizer:
    thresholds: List[float]
    space_fmt: str = "<lhspace-%d>"

    def quantize(self, value: npt.ArrayLike):
        return np.digitize(value, self.thresholds) + 1
    
    def to_categorical_space(self, value: Union[float,npt.ArrayLike]) -> Union[str, np.char.chararray]:
        x = np.digitize(value, self.thresholds) + 1
        if np.ndim(value) == 0:
            return self.space_fmt % x
        else:
            return np.char.array(self.space_fmt) % x
        
    def __call__(self, value):
        return self.to_categorical_space(value)

    def __repr__(self) -> str:
        return f"Quantizer with bins {self.thresholds}"