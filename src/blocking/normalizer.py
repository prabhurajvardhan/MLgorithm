
import re
import unicodedata


LEGAL_SUFFIXES = {
    "inc", "incorporated",
    "llc",
    "ltd", "limited",
    "corp", "corporation",
    "co", "company",
    "plc",
    "pvt", "private",
    "lp", "llp",
    "l l c",
    "l t d",
}


ABBREVIATIONS = {
    # address
    "rd": "road",
    "rd.": "road",
    "st": "street",
    "st.": "street",
    "str": "street",
    "str.": "street",
    "ave": "avenue",
    "ave.": "avenue",
    "av": "avenue",
    "blvd": "boulevard",
    "blvd.": "boulevard",
    "dr": "drive",
    "dr.": "drive",
    "ln": "lane",
    "ln.": "lane",
    "hwy": "highway",
    "hwy.": "highway",
    "pkwy": "parkway",
    "pkwy.": "parkway",
    "ct": "court",
    "ct.": "court",
    "pl": "place",
    "pl.": "place",
    "sq": "square",
    "sq.": "square",
    "mt": "mount",
    "apt": "apartment",
    "apt.": "apartment",
    "bldg": "building",
    "bldg.": "building",
    "fl": "floor",
    "fl.": "floor",

    # business
    "ctr": "center",
    "ctr.": "center",
    "centre": "center",
    "intl": "international",
    "intl.": "international",
    "mkt": "market",
    "mkt.": "market",
    "med": "medical",
    "med.": "medical",
    "tech": "technology",
    "tech.": "technology",
    "mgmt": "management",
    "mgmt.": "management",
    "svc": "service",
    "svc.": "service",
    "svcs": "services",
    "dept": "department",
    "dept.": "department",
    "assoc": "associates",
    "assoc.": "associates",
    "bros": "brothers",
    "bros.": "brothers",
}


def ascii_text(value):
    if value is None:
        return ""

    text = str(value)

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        ch for ch in text
        if not unicodedata.combining(ch)
    )

    return text


def normalize_text(value):
    """
    General text normalization.

    Keeps alphanumeric information while normalizing:
    case, Unicode, ampersands, punctuation and whitespace.
    """
    text = ascii_text(value).lower()

    # "&" is semantically equivalent to "and" in many
    # business names.
    text = re.sub(r"\s*&\s*", " and ", text)

    # Convert common separators to spaces.
    text = re.sub(r"[/|,_;:+]+", " ", text)

    # Keep letters/numbers/spaces.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_tokens(value, remove_legal_suffixes=False):
    """
    Return normalized token list.
    """
    text = normalize_text(value)

    tokens = text.split()

    expanded = []

    for token in tokens:
        replacement = ABBREVIATIONS.get(token, token)
        expanded.extend(replacement.split())

    tokens = expanded

    if remove_legal_suffixes:
        tokens = [
            token for token in tokens
            if token not in LEGAL_SUFFIXES
        ]

    return tokens


def normalize_name(value):
    """
    Business-name normalization.

    Expands abbreviations and removes legal suffixes.
    """
    tokens = normalize_tokens(
        value,
        remove_legal_suffixes=True
    )

    return " ".join(tokens)


def compact_name(value):
    """
    Aggressive normalized representation useful for
    exact/near-exact blocking.
    """
    return re.sub(
        r"[^a-z0-9]",
        "",
        normalize_name(value)
    )


def normalized_initials(value):
    """
    First character of meaningful normalized tokens.
    """
    tokens = normalize_tokens(
        value,
        remove_legal_suffixes=True
    )

    return "".join(
        token[0]
        for token in tokens
        if token
    )


def normalized_ngrams(value, n=3):
    """
    Character n-grams over compact normalized name.
    """
    text = compact_name(value)

    if len(text) < n:
        return []

    return [
        text[i:i+n]
        for i in range(len(text) - n + 1)
    ]
