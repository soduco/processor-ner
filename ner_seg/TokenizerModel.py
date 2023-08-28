from transformers import AutoTokenizer
from .layout import BREAKS, QUANTIZED_INDENTS, ENTRY, TEXTLINE

NEW_TOKENS = set(BREAKS.values())

# Space tokens to encode left/right spaces tags <[L|R]SPACE.../>
N_SPACE_CLASSES = 10
SPACE_TOKENS = [
    v % q
    for q in range(1, N_SPACE_CLASSES + 1)
    for v in QUANTIZED_INDENTS.values()
]
NEW_TOKENS.update(SPACE_TOKENS)
NEW_TOKENS.update(ENTRY.values())
NEW_TOKENS.update([TEXTLINE])

DEFAULT_TOKENIZER_MODEL = "HueyNemud/das22-10-camembert_pretrained"
TOKENIZER_MODEL = "HueyNemud/icdar23-entrydetector_labelledtext_breaks_indents_left_diff_right_ref"



def new_layout_tokenizer(from_pretrained: str = DEFAULT_TOKENIZER_MODEL):
    hf_tokenizer = AutoTokenizer.from_pretrained(from_pretrained)
    hf_tokenizer.add_tokens(list(NEW_TOKENS))
    return hf_tokenizer


layout_tokenizer = new_layout_tokenizer(TOKENIZER_MODEL)
