
from argparse import ArgumentParser, FileType

import pathlib
import glob
import itertools
from . import TextEntityClassification, InputLineStreamGenerator, EntrySplitter
from .TextProcessor import Entry


# Parser definition
parser = ArgumentParser(description='NER command line interface')
parser.add_argument("-i", "--input-dir", required=True, type=pathlib.Path)
parser.add_argument("-o", "--output-file", required=False, type=FileType('w', encoding='UTF-8'))
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


## Export XML / JSON
for (dir, page), g in groups:
    if args.output_file:
        print(f'<PAGE dir="{dir}" page="{page}">', file=args.output_file)

    json_file = None


    for i, e in enumerate(g):
        if args.output_file:
            print(f'<ENTRY>', file=args.output_file)
            print(e.ner_xml, file=args.output_file, end = "")
            print("</ENTRY>", file=args.output_file)



    if args.output_file:
        print(f'</PAGE>', file=args.output_file)








