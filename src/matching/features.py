
from rapidfuzz import fuzz

from src.blocking.normalizer import (
    normalize_text,
    normalize_name,
    compact_name,
)


def clean_text(text):
    return normalize_text(text)


def get_tokens(text):
    return set(normalize_name(text).split())


def jaccard_similarity(text1, text2):
    tokens1 = get_tokens(text1)
    tokens2 = get_tokens(text2)

    if not tokens1 and not tokens2:
        return 1.0

    if not tokens1 or not tokens2:
        return 0.0

    return len(tokens1 & tokens2) / len(tokens1 | tokens2)


def levenshtein_similarity(text1, text2):
    text1 = normalize_name(text1)
    text2 = normalize_name(text2)

    if not text1 and not text2:
        return 1.0

    if not text1 or not text2:
        return 0.0

    return fuzz.ratio(text1, text2) / 100.0


def token_sort_similarity(text1, text2):
    text1 = normalize_name(text1)
    text2 = normalize_name(text2)

    if not text1 and not text2:
        return 1.0

    if not text1 or not text2:
        return 0.0

    return fuzz.token_sort_ratio(text1, text2) / 100.0


def exact_match(text1, text2):
    text1 = normalize_name(text1)
    text2 = normalize_name(text2)

    return int(text1 == text2)


def build_pair_features(s1_row, other_row):

    name1 = s1_row["business_name"]
    name2 = other_row["business_name"]

    address1 = s1_row["business_address"]
    address2 = other_row["business_address"]

    country1 = s1_row["country"]
    country2 = other_row["country"]

    return {
        "name_jaccard":
            jaccard_similarity(name1, name2),

        "name_levenshtein":
            levenshtein_similarity(name1, name2),

        "name_token_sort":
            token_sort_similarity(name1, name2),

        "name_exact":
            exact_match(name1, name2),

        "address_jaccard":
            jaccard_similarity(address1, address2),

        "address_levenshtein":
            levenshtein_similarity(address1, address2),

        "address_token_sort":
            token_sort_similarity(address1, address2),

        "address_exact":
            exact_match(address1, address2),

        "country_match":
            int(
                normalize_text(country1)
                ==
                normalize_text(country2)
            ),
    }
}
