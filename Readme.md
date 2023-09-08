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
                        Upper bound of the range, inclusive. Assumes file names match pattern `.*?[0-9]+.json`.
  --inplace             Edit inplace the json files to add entries inside.
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

## Docker
To generate a Docker image ready to run on any Linux platform and use it, follow the process below.

1. Build the image:  
  `docker build -t soduco/processor-ner .`
2. (Opt.) Export image from build machine and import it into processing machines:  
  `docker image save soduco/processor-ner | pigz > soduco-processor-ner.tar.gz`  
  … copy the image to the target machine and then …
  `docker image load < soduco-processor-ner.tar.gz`
3. Create a container
4. Launch the process, using some bind-mounted input and output directories:  
  `docker run --name soduco-processor-ner --rm -it -v /work/soduco/202308-reprocess/input/DIR:/input:ro -v /work/soduco/202308-reprocess/output:/output soduco/processor-ner -o /output/DIR-RLO:RHI.xml -f RLO -u RHI` 
  *Note that you only need to provide the `--output-file`, `--range-from` and `--range-upto` on the command line.*

