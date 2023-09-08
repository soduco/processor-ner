import itertools
import re
from transformers import pipeline
from . import TokenizerModel, ClassificationModel
from typing import Sequence, List, Iterator, Dict, Tuple, Generator, Generic, TypeVar
from dataclasses import dataclass, field
from torch.utils.data import IterableDataset
from .InputStreamGenerator import LineInfo

T = TypeVar("T")


class CacheGeneratorWrapper(IterableDataset, Generic[T]):
    '''
    This class is a one-time cache, as soon as an element is retrieve, it is removed from the cache
    (It is used to forward line information in a stream process)
    '''

    def __init__(self, dataset: Iterator[T]):
        self._ds = dataset
        self._cache : Dict[int, T] = {}

    def __iter__(self):
        for i, e in enumerate(self._ds):
            self._cache[i] = e
            yield e

    def __getitem__(self, i):
        return self._cache.pop(i)
    



def chunks(seq: Iterator[T], chunksize: int, overlap: int = 0) -> Iterator[List[T]]:
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


@dataclass
class TextChunk:
    lines: List[LineInfo]
    output_lines: List[str] = None
    _text: str = None


    def text(self) -> str:
        if self._text is None:
            self._text = "<break>".join(x.text for x in self.lines)
        return self._text
    

    def __iter__(self) -> Iterator[Tuple[LineInfo, str]]:
        return zip(self.lines, self.output_lines)
    


_rexp = re.compile("<(.hspace-.)>")

def _postprocess_chunk(chunk: TextChunk, ne_list) -> TextChunk:
    # 1. Get the xml encoded strings 
    xml = _get_xml_string(chunk.text(), map(_NamedEntity.from_huggingface, ne_list))

    # 2. Remove visual tokens
    xml = _rexp.sub("", xml) 

    # 3. Split
    chunk.output_lines = xml.split("<break>")

    return chunk


    

def _skipoverlap(lines: List[T], chuncksize: int, overlap: int) -> Iterator[T]:
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


class _IterDataset(IterableDataset):
    def __init__(self, generator : Iterator[T]):
        self.generator = generator

    def __iter__(self) -> Iterator[T]:
        return self.generator


def TextEntityClassification(lines: Iterator[LineInfo], overlap = 4, chunk_size = 20) -> Iterator[Tuple[LineInfo, str]]:
    """Perform NER extraction from a text stream.
    (Fixme: should the input be a io.TextIOBase with readline support ?)

    Args:
        lines (Sequence[str]): Sequence of lines (a line is word sequence with visual space tokens inluded <[rl]hspace-x>) 
        overlap (int, optional): _description_. Defaults to 4.
        chunk_size (int, optional): _description_. Defaults to 20.

    Returns:
        Iterator[t]: The lines of where the line t is the tuple (input_text, lineinfo, ner output)
    """
    ner = pipeline("ner", model=ClassificationModel.classification_model, tokenizer=TokenizerModel.layout_tokenizer, aggregation_strategy="simple")


    # Create the text generator for the lines
    textchunks = (TextChunk(textlines) for textlines in chunks(lines, chunk_size, overlap))

    # Cache the generated text batches to retrieve the input text (Lazy)
    gen = CacheGeneratorWrapper(textchunks)

    #
    textonly = _IterDataset(x.text() for x in gen)

    # Compute the ner on each text chunk (Lazy)
    xmls = ( _postprocess_chunk(gen[i], entities) for i,entities in enumerate(ner(textonly)) )

    # Remove overlaps
    xmls = _skipoverlap(itertools.chain.from_iterable(xmls), chunk_size, overlap)

    return xmls 

@dataclass
class Entry:
    elements: List[LineInfo] = field(default_factory=list) # List of children ids 
    text_ocr: str = ""
    ner_xml: str = ""

    def get_dir(self):
        return self.elements[0].directory
    
    def get_page(self):
        return self.elements[0].page
    
    def get_group(self):
        e = self.elements[0]
        return (e.directory, e.page)


def EntrySplitter(lines: Iterator[Tuple[LineInfo, str]]) -> Iterator[Entry]:
    """

    Args:
        lines (Iterator[Tuple[LineInfo, str]]): 

    Yields:
        Iterator[Entry]: 
    """
    entry = None
    for lineinfo, lineout in lines:

        if lineout.startswith("<ENTRY>"):
            if entry is not None:
                yield entry # FLUSH (unfinished) previous entry
            entry = Entry()
        else:
            entry = entry or Entry()
    
        entry.text_ocr += lineinfo.text + "\n"
        entry.ner_xml += lineout.removeprefix("<ENTRY>").removesuffix("</ENTRY>") + "\n"
        entry.elements.append(lineinfo) 


        if lineout.endswith("</ENTRY>"):
            yield entry # FLUSH current entry
            entry = None

    ## Flush last entry
    if entry is not None:
        yield entry
    


