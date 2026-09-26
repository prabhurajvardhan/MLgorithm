
import re
from rapidfuzz import fuzz


def clean_text(text):
    """Convert text to lowercase and remove extra spaces."""
    if text is None:
        return ""

    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_tokens(text):
    """Split text into simple words."""
    text = clean_text(text)

    tokens = re.findall(r"\b\w+\b", text)

    return set(tokens)


def jaccard_similarity(text1, text2):
    """Calculate Jaccard similarity between two texts."""
    tokens1 = get_tokens(text1)
    tokens2 = get_tokens(text2)

    if not tokens1 and not tokens2:
        return 1.0

    if not tokens1 or not tokens2:
        return 0.0

    common = tokens1.intersection(tokens2)
    total = tokens1.union(tokens2)

    return len(common) / len(total)


def levenshtein_similarity(text1, text2):
    """Calculate character-level similarity."""
    text1 = clean_text(text1)
    text2 = clean_text(text2)

    if not text1 and not text2:
        return 1.0

    if not text1 or not text2:
        return 0.0

    return fuzz.ratio(text1, text2) / 100


def token_sort_similarity(text1, text2):
    """Compare texts after sorting their words."""
    text1 = clean_text(text1)
    text2 = clean_text(text2)

    if not text1 and not text2:
        return 1.0

    if not text1 or not text2:
        return 0.0

    return fuzz.token_sort_ratio(text1, text2) / 100


def exact_match(text1, text2):
    """Check whether two values are exactly the same."""
    text1 = clean_text(text1)
    text2 = clean_text(text2)

    if text1 == text2:
        return 1

    return 0


def build_pair_features(s1_row, other_row):
    """
    Create numerical features for one S1-S2/S3 pair.
    """

    name1 = s1_row["business_name"]
    name2 = other_row["business_name"]

    address1 = s1_row["business_address"]
    address2 = other_row["business_address"]

    country1 = s1_row["country"]
    country2 = other_row["country"]

    features = {
        "name_jaccard": jaccard_similarity(name1, name2),

        "name_levenshtein": levenshtein_similarity(
            name1, name2
        ),

        "name_token_sort": token_sort_similarity(
            name1, name2
        ),

        "name_exact": exact_match(
            name1, name2
        ),

        "address_jaccard": jaccard_similarity(
            address1, address2
        ),

        "address_levenshtein": levenshtein_similarity(
            address1, address2
        ),

        "address_token_sort": token_sort_similarity(
            address1, address2
        ),

        "address_exact": exact_match(
            address1, address2
        ),

        "country_match": exact_match(
            country1, country2
        )
    }

    return features
