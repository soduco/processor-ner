
from argparse import ArgumentParser, FileType

import pathlib
import glob
import re
from . import TextEntityClassification, InputLineStreamGenerator


# Range validation utils
def extract_filename_index(filename: str|pathlib.Path) -> int|None:
    # note the non-greedy (minimal) lazy matching for the non-numeric (left) part using `*?`.
    match: re.Match|None = re.match(r".*?([0-9]+).json", filename)
    if match is None:
        return None
    return int(match.group(1))

def match_range_from(from_: int, index: int|None) -> bool:
    # note: we discard non-matching filenames
    return index is not None and index >= from_

def match_range_upto(upto: int, index: int|None) -> bool:
    # note: we discard non-matching filenames
    return index is not None and (upto == -1 or index <= upto)

# Parser definition
parser = ArgumentParser(description='NER command line interface')
parser.add_argument("-i", "--input-dir", required=True, type=pathlib.Path)
parser.add_argument("-o", "--output-file", required=True, type=FileType('w', encoding='UTF-8'))
parser.add_argument("-f", "--range-from", required=False, default=0, type=int, help="Lower bound of the range, inclusive. Assumes file names match pattern `.*?[0-9]+.json`.")
parser.add_argument("-u", "--range-upto", required=False, default=-1, type=int, help="Upper bound of the range, inclusive. Assumes file names match pattern `.*?[0-9]+.json`. -1 means no limit.")


# Parse cli and check range arguments
args = parser.parse_args()
if args.range_from < 0:
    raise ValueError(f"`--range-from` argument must be >= 0. Got range_from={args.range_from} instead.")
if args.range_upto < -1:
    raise ValueError(f"`--range-upto` argument must be >= 0 or == -1. Got range_upto={args.range_upto} instead.")
if args.range_upto != -1 and args.range_upto < args.range_from:
    raise ValueError(f"When specifying a `--range-upto` argument, it must be must be >= the `--range-from` argument. Got range_upto={args.range_upto} < range_from={args.range_from} instead.")

# Collect and filter file names
jsons = sorted(glob.glob("**/*.json", root_dir=args.input_dir, recursive=True))
jsons = [ args.input_dir / j 
         for j, idx in zip(jsons, [extract_filename_index(e) for e in jsons])
         if match_range_from(args.range_from, idx) and match_range_upto(args.range_upto, idx)]

# Process
input_line_stream = InputLineStreamGenerator(jsons)
output_line_stream = TextEntityClassification(input_line_stream)

for line in output_line_stream:
    print(line, file=args.output_file)



