Transform jsons into a raw xml file

Input format:

* A directory with layout ``{directory}/{####}.json``

Output format 
* XML


## Usage

```
usage: __main__.py [-h] -i INPUT_DIR -o OUTPUT_FILE

NER command line interface

options:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --input-dir INPUT_DIR
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
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
