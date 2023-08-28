from transformers import AutoModelForTokenClassification

TOKEN_CLASSIFICATION_MODEL = "HueyNemud/icdar23-entrydetector_labelledtext_breaks_indents_left_diff_right_ref"


def _new_layout_model(from_pretrained: str = TOKEN_CLASSIFICATION_MODEL):
    return AutoModelForTokenClassification.from_pretrained(from_pretrained)



classification_model = _new_layout_model()