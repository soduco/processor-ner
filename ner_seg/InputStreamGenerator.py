import json
import pathlib
from tqdm import tqdm
from .Quantizer import Quantizer
from typing import Iterator


def InputLineStreamGenerator(jsonfiles: list[pathlib.Path]) -> Iterator[str]:
    lspaceQ = Quantizer([-0.01, 0.01], space_fmt="<lhspace-%d>")
    rspaceQ = Quantizer([0.05, 0.09], space_fmt="<rhspace-%d>")
    for path in tqdm(jsonfiles):
        with open(path) as f:
            js = json.load(f)
            for e in js:
                if e["type"] == "LINE":
                    ltoken = lspaceQ(e["margin-left-relative"])
                    rtoken = rspaceQ(e["margin-right"])
                    line = ltoken + e["text"] + rtoken
                    yield line





