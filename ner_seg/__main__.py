
from argparse import ArgumentParser, FileType

import pathlib
import glob
import itertools
import json
import numpy as np
import sys
from typing import TextIO, Iterator
from . import TextEntityClassification, InputLineStreamGenerator, EntrySplitter
from .TextProcessor import Entry


# Parser definition
parser = ArgumentParser(description='NER command line interface')
parser.add_argument("-i", "--input-dir", required=True, type=pathlib.Path)
parser.add_argument("-o", "--output-file", required=False, default=None, type=FileType('w', encoding='UTF-8'))
parser.add_argument("-f", "--range-from", required=False, default=0, type=int, help="Lower bound of the range, inclusive. Assumes file names match pattern `**/[0-9]+.json`.")
parser.add_argument("-u", "--range-upto", required=False, default=float("+inf"), type=int, help="Upper bound of the range, inclusive. Assumes file names match pattern `**/[0-9]+.json`. -1 means no limit.")
parser.add_argument("--inplace", action="store_true", help="Edit the json inplace ")



# Parse cli and check range arguments
args = parser.parse_args()
if args.range_from < 0:
    raise ValueError(f"`--range-from` argument must be >= 0. Got range_from={args.range_from} instead.")
if args.range_upto < 0:
    raise ValueError(f"`--range-upto` argument must be >= 0. Got range_upto={args.range_upto} instead.")
if args.range_from >= args.range_upto:
    raise ValueError(f"When specifying a `--range-upto` argument, it must be must be >= the `--range-from` argument. Got range_upto={args.range_upto} < range_from={args.range_from} instead.")

# Collect and filter file names
jsons = sorted(glob.glob("**/*.json", root_dir=args.input_dir, recursive=True))
jsons = [ args.input_dir / j for j in jsons if args.range_from <= int(pathlib.Path(j).stem) <= args.range_upto ]

# Process
input_line_stream  = InputLineStreamGenerator(jsons)
output_line_stream = TextEntityClassification(input_line_stream)

# Group entries
entry_stream = EntrySplitter(output_line_stream)

# Group by (dir/page)
groups       = itertools.groupby(entry_stream, key=Entry.get_group)


def export_entries(entries: Iterator[Entry], js: dict|None, out: TextIO|None, dir: str, page: int):
    if js:
        rev = { e["id"] : e for e in js }

    
    if out:
        print(f'<PAGE dir="{dir}" page="{page}">', file=out)

    id = 2000
    for i,e in enumerate(entries):
        if js:
            first = rev[e.elements[0].item]
            boxes = np.array([ rev[x.item]["box"] for x in e.elements if x.page == page and rev[x.item]["parent"] == first["parent"]])
            boxes[:,2] += boxes[:,0]
            boxes[:,3] += boxes[:,1]
            x1 = boxes[:,0].min()
            y1 = boxes[:,1].min()
            x2 = boxes[:,2].max()
            y2 = boxes[:,3].max()

            entry = { 
                "id":  id + i,
                "children" : [ f"{x.directory}-{x.page:04}-{x.item}" for x in e.elements ],
                "text_ocr" : e.text_ocr,
                "ner_xml" : e.ner_xml,
                "parent" : first["parent"],
                "box" : (x1, y1, x2-x1, y2-y1),
                "type" : "ENTRY"
            }
            js.append(entry)

        if out:
            print(f'<ENTRY>', file=out)
            print(e.ner_xml, file=out, end = "")
            print("</ENTRY>", file=out)

    if out:
        print(f'</PAGE>', file=out)
    




## Export XML / JSON
for (dir, page), g in groups:

    json_file = None
    if args.inplace:
        with open(args.input_dir / f'{dir}/{page:04}.json') as f:
            json_file = json.load(f)

    export_entries(g, json_file, args.output_file, dir, page)

    if args.inplace:
        with open(args.input_dir / f'{dir}/{page:04}.json', 'w', encoding='utf-8') as f:
            json.dump(json_file, f, ensure_ascii=False, indent=True)








