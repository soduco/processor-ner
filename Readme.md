Transform jsons into a raw xml file

Input format:

* A directory with layout ``{directory}/{####}.json``

Output format 
* XML


## Usage

```
usage: __main__.py [-h] -i INPUT_DIR -o OUTPUT_FILE [-f RANGE_FROM] [-u RANGE_UPTO]

NER command line interface

options:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --input-dir INPUT_DIR
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
  -f RANGE_FROM, --range-from RANGE_FROM
                        Lower bound of the range, inclusive. Assumes file names match pattern `.*?[0-9]+.json`.
  -u RANGE_UPTO, --range-upto RANGE_UPTO
                        Upper bound of the range, inclusive. Assumes file names match pattern `.*?[0-9]+.json`. -1 means no limit.
```

Example, running the command:

```sh
pipenv run python -m ner_seg -i tests -o -
```

will stream the xml on the standard output:

```
<ACT>pot, broches de cuisinières, et tout
ce qui concerne cette partie</ACT>, <LOC>Tem-
ple</LOC>, <CARDINAL>69</CARDINAL>.</ENTRY>
<ENTRY><PER>Caron (P.</PER>), <ACT>ingénieur-mécanicien</ACT>,
ci-devant <LOC>Faub. -St-Martin</LOC>, <CARDINAL>147</CARDINAL>,
...
```
