
from argparse import ArgumentParser, FileType

import pathlib
import glob
from . import TextEntityClassification, InputLineStreamGenerator

def process():
    pass




parser = ArgumentParser(description='NER command line interface')
parser.add_argument("-i", "--input-dir", required=True, type=pathlib.Path)
parser.add_argument("-o", "--output-file", required=True, type=FileType('w', encoding='UTF-8'))


args = parser.parse_args()
jsons = sorted(glob.glob("**/*.json", root_dir=args.input_dir, recursive=True))
jsons = [ args.input_dir / j for j in jsons]

input_line_stream = InputLineStreamGenerator(jsons)
output_line_stream = TextEntityClassification(input_line_stream)

for line in output_line_stream:
    print(line, file=args.output_file)



