"""Parsing and normalization of people and company names."""

import re
import unicodedata

# A separator is a comma or an ampersand, optionally followed by "and"
# ("A, B, and C"), or the standalone word "and" ("A and B"), in any case.
# Words that merely contain "and" (e.g. "Anderson") are left untouched.
_NAME_SEPARATOR = re.compile(r"\s*[,&]\s*(?:and\s+)?|\s+and\s+", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")
_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


def clean_name(name: str) -> str:
    r"""Normalize the Unicode form and the whitespace of a name.

    Args:
        name: Raw name.

    Returns:
        The name in NFKC form, trimmed, with inner whitespace collapsed.

    Examples:
        >>> clean_name("  Joel\u00a0  Silver ")
        'Joel Silver'
    """
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFKC", name)).strip()


def slugify(name: str) -> str:
    """Return the slug that identifies a name.

    The slug ignores case, spacing, accents and punctuation, so different
    spellings of the same name share one slug.

    Args:
        name: Raw name.

    Returns:
        Lower-case ASCII words joined by hyphens. Names without any letter or
        digit fall back to their case-folded form.

    Examples:
        >>> slugify("JOEL  silver")
        'joel-silver'
        >>> slugify("José Ferrer") == slugify("Jose Ferrer")
        True
        >>> slugify("Robert W. Cort") == slugify("Robert W Cort")
        True
    """
    decomposed = unicodedata.normalize("NFKD", clean_name(name))
    ascii_name = decomposed.encode("ascii", "ignore").decode().casefold()
    return _NON_ALPHANUMERIC.sub("-", ascii_name).strip("-") or name.casefold()


def split_names(raw: str) -> tuple[str, ...]:
    """Split a list of names written in natural language.

    Names are cleaned with :func:`clean_name`; repeated names (compared with
    :func:`slugify`) are dropped, keeping the best spelling according to
    :func:`is_better_spelling`.

    Args:
        raw: Names separated by commas, ``&`` and/or ``and``.

    Returns:
        The individual names, in their original order.

    Examples:
        >>> split_names("ALLAN CARR, Bob Cavallo AND Joe Ruffalo & Allan Carr")
        ('Allan Carr', 'Bob Cavallo', 'Joe Ruffalo')
    """
    names: dict[str, str] = {}
    for part in _NAME_SEPARATOR.split(raw):
        if not (name := clean_name(part)):
            continue
        key = slugify(name)
        if key not in names or is_better_spelling(name, names[key]):
            names[key] = name
    return tuple(names.values())


def is_better_spelling(candidate: str, current: str) -> bool:
    """Tell whether ``candidate`` is a better-cased spelling of ``current``.

    A mixed-case spelling ("Joel Silver") is preferred over one written
    entirely in upper or lower case ("JOEL SILVER", "joel silver").

    Args:
        candidate: Newly seen spelling.
        current: Spelling currently stored.

    Returns:
        ``True`` when ``candidate`` should replace ``current``.
    """

    def is_single_case(name: str) -> bool:
        return name in (name.upper(), name.lower())

    return is_single_case(current) and not is_single_case(candidate)
