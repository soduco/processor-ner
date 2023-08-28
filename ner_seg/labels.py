NO_ENT_LBL = "O"
ENTRY_BEGIN = "I-EBEGIN"
ENTRY_END = "I-EEND"

LABELS_IDS = {
    NO_ENT_LBL: 0,  # The labeled token does not belong to any known entity
    "I-LOC": 1,  # An address, like "rue du Faub. St.-Antoine"
    "I-PER": 2,  # A person, like "Baboulinet (Vincent)"
    "I-MISC": 3,  # Not used but found in the base model
    "I-ORG": 4,  # Not used but found in the base model
    "I-CARDINAL": 5,  # Not used but found in the base model
    "I-ACT": 6,  # An activity, like "plombier-devin"
    "I-TITRE": 7,  # A person's encoded title, like "O. ::LH::" for "Officier de la Légion d'Honneur"
    "I-FT": 8,  # A feature type, like "fabrique" or "dépot" in front of addresses.
    ENTRY_BEGIN: 9,  # A new directory entry starts here
    ENTRY_END: 10,  # A directory entry ends here
}


ENTITY_XML_TAGS = ["PER", "LOC", "CARDINAL", "FT", "TITRE", "ACT"]