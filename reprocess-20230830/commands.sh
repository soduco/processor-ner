cat annuaires-plages.tsv | \
parallel \
    --bar \
    -S2/jcomp0{1..5}.lrde.epita.fr \
    --colsep '\t' \
    docker run \
        --rm \
        --name soduco-processor-ner{#} \
        -v /work/soduco/202308-reprocess/input/{1}:/input:ro \
        -v /work/soduco/202308-reprocess/output:/output \
        soduco/processor-ner \
            -o /output/{1}-{2}:{3}.xml -f {2} -u {3}