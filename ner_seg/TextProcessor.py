import itertools
import re
from transformers import pipeline
from . import TokenizerModel, ClassificationModel
from typing import Sequence, List, Iterator, Dict, Tuple
from dataclasses import dataclass
from torch.utils.data import IterableDataset


class CacheGeneratorWrapper(IterableDataset):
    '''
    This class is a one-time cache, as soon as an element is retrieve, it is removed from the cache
    (It is used to forward line information in a stream process)
    '''

    def __init__(self, dataset):
        self._ds = dataset
        self._cache = {}

    def __iter__(self):
        for i, e in enumerate(self._ds):
            self._cache[i] = e
            yield e

    def __getitem__(self, i):
        return self._cache.pop(i)
    



def chunks(seq, chunksize: int, overlap: int = 0):
    '''
    >>> list(chunks(range(13), 4, 2))
    Out[34]: 
    [[0, 1, 2, 3], [2, 3, 4, 5], [4, 5, 6, 7], [6, 7, 8, 9], [8, 9, 10, 11], [10, 11, 12]]
    '''
    it = iter(seq)

    chunk = list(itertools.islice(it, chunksize))
    yield chunk

    while len(chunk) == chunksize:
        if overlap > 0:
            chunk = chunk[-overlap:] + list(itertools.islice(it, chunksize - overlap))
        else: 
            chunk = list(itertools.islice(it, chunksize))
        yield chunk


@dataclass
class _NamedEntity:
    """A unified representation of a Named Entity"""

    label: str
    score: float
    start: int
    end: int
    text: str

    ##
    # Factory methods
    ##


    @staticmethod
    def from_spacy(ent: "spacy.tokens.span.Span") -> "_NamedEntity":
        return _NamedEntity(
            label=ent.label_,
            start=ent.start_char,
            end=ent.end_char,
            text=ent.text,
            score=None,
        )

    @staticmethod
    def from_huggingface(ent: dict) -> "_NamedEntity":
        return _NamedEntity(
            label=ent["entity_group"],
            start=ent["start"],
            end=ent["end"],
            text=ent["word"],
            score=ent["score"],
        )

def _get_xml_string(source_text: str, named_entities: List[_NamedEntity], espace_html = False) -> str:
    """Builds a XML representation of a directory entry from the list of named entities detected inside.
    Entites are assumed to be in order of appearance in the source text.

    Args:
        source_text (str): The entry text.
        named_entities (List[_NamedEntity]): The named entities detected in the source text.

    Returns:
        str: A XML string representing this entry with its named entities.
    """
    if espace_html:
        import html
        htmlescape = lambda x: html.escape(x, quote=False)
    else:
        htmlescape = lambda x: x

    def xmlize(tag, text):
        match tag:
            case "EBEGIN": return "<ENTRY>"
            case "EEND": return "</ENTRY>"
            case _: return f"<{tag}>{htmlescape(text)}</{tag}>"


    cursor = 0
    parts = []
    for ent in named_entities:
        if ent.start > cursor:
            skipped_txt = htmlescape(source_text[cursor : ent.start])
            parts.append(skipped_txt)
        span = source_text[ent.start : ent.end]

        # Patch for BERT : the span may start with a whitespace or a \n.
        # In this case the leading character is moved in front of the named entity
        if span.startswith(("\t", " ", "\n")):
            parts.append(span[0])
            span = span[1:]

        xml_ent = xmlize(ent.label, span)
        parts.append(xml_ent)
        cursor = ent.end

    if cursor < len(source_text):
        last_words = htmlescape(source_text[cursor:])
        parts.append(last_words)

    return "".join(parts)


def _postprocess_result(results: List[Tuple[str, List[_NamedEntity]]]):
    rexp = re.compile("<(.hspace-.)>")

    # 1. Get the xml encoded strings 
    xmls = ( _get_xml_string(src, map(_NamedEntity.from_huggingface, ne_list)) for src, ne_list in results)

    # 2. Remove visual tokens
    xmls = map(lambda x: rexp.sub("", x), xmls)

    # 3. Split
    xmls = map(lambda x: x.split("<break>"), xmls)

    return xmls
    

def _skipoverlap(lines: List[str], chuncksize: int, overlap: int) -> Iterator[str]:
    """
    We ensure that:
    I = range(i)
    K = InputStreamGenerator.chunks(I, 20, 4)
    R = InputStreamGenerator._skipoverlap(itertools.chain.from_iterable(K), 20, 4)
    assert list(I) == list(R)

    Args:
        lines (List[str]): _description_
        chuncksize (int): _description_
        overlap (int): _description_

    Yields:
        Iterator[str]: _description_
    """
    it = iter(lines)
    skipend = overlap // 2
    skipstart = 0
    chunk = list(itertools.islice(it, chuncksize))

    while len(chunk) == chuncksize:
        for e in itertools.islice(chunk, skipstart, chuncksize - skipend):
            yield e
        chunk = list(itertools.islice(it, chuncksize))
        skipstart = overlap - skipend

    for e in itertools.islice(chunk, skipstart, chuncksize):
        yield e



def TextEntityClassification(lines: Sequence[str], overlap = 4, chunk_size = 20) -> Iterator[str]:
    """Perform NER extraction from a text stream.
    (Fixme: should the input be a io.TextIOBase with readline support ?)

    Args:
        lines (Sequence[str]): Sequence of lines (a line is word sequence with visual space tokens inluded <[rl]hspace-x>) 
        overlap (int, optional): _description_. Defaults to 4.
        chunk_size (int, optional): _description_. Defaults to 20.

    Returns:
        Iterator[str]: The lines of text with ner tags included
    """
    ner = pipeline("ner", model=ClassificationModel.classification_model, tokenizer=TokenizerModel.layout_tokenizer, aggregation_strategy="simple")

    # Create the text generator for the lines
    textchunks = ("<break>".join(textlines) for textlines in chunks(lines, chunk_size, overlap))

    # Cache the generated text batches to retrieve the input text (Lazy)
    gen = CacheGeneratorWrapper(textchunks)

    # Compute the ner on each text chunk (Lazy)
    results = ( (gen[i], entities) for i,entities in enumerate(ner(gen)) )

    # Compute the xml of each chunck
    xmls = _postprocess_result(results)

    # Remove overlaps
    xmls = _skipoverlap(itertools.chain.from_iterable(xmls), chunk_size, overlap)

    return xmls 