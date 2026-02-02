# modules/tokenizer.py

import re
from dataclasses import dataclass, field

# -----------------------------
# Token regexes (canonical)
# -----------------------------
INLINE_RE = re.compile(r"\{\{([^}\[\]]+)(?:\[([^\]]+)\])?\}\}")
BLOCK_RE  = re.compile(r"<<([^>\[\]]+)(?:\[([^\]]+)\])?>>")
SYSTEM_RE = re.compile(r"\[\[([^\]]+)\]\]")

# -----------------------------
# Token models
# -----------------------------
@dataclass
class Token:
    kind: str              # TEXT | VAR_INLINE | VAR_BLOCK | SYSTEM
    raw: str               # full matched text (debug only)
    name: str | None       # normalized token name
    flags: set[str]
    index: int             # sequential token index

@dataclass
class VariableMeta:
    occurrences: int = 0
    flags_seen: set[str] = field(default_factory=set)
    is_derived: bool = False

@dataclass
class BlockMeta:
    occurrences: int = 0

@dataclass
class TokenStream:
    tokens: list[Token]
    variables: dict[str, VariableMeta]   # {{inline}}
    blocks: dict[str, BlockMeta]          # <<dynamic>>
    system_vars: dict[str, int]           # [[system]]

# -----------------------------
# Tokenizer
# -----------------------------
def tokenize(text: str) -> TokenStream:
    tokens: list[Token] = []
    variables: dict[str, VariableMeta] = {}
    blocks: dict[str, BlockMeta] = {}
    system_vars: dict[str, int] = {}

    pos = 0
    idx = 0
    length = len(text)

    while pos < length:
        matches = []

        for regex, kind in (
            (INLINE_RE, "VAR_INLINE"),
            (BLOCK_RE,  "VAR_BLOCK"),
            (SYSTEM_RE, "SYSTEM"),
        ):
            m = regex.search(text, pos)
            if m:
                matches.append((m.start(), m, kind))

        # No more tokens
        if not matches:
            tokens.append(Token(
                kind="TEXT",
                raw=text[pos:],
                name=None,
                flags=set(),
                index=idx
            ))
            break

        start, match, kind = min(matches, key=lambda x: x[0])

        # Emit intervening text
        if start > pos:
            tokens.append(Token(
                kind="TEXT",
                raw=text[pos:start],
                name=None,
                flags=set(),
                index=idx
            ))
            idx += 1

        raw = match.group(0)
        name = match.group(1)
        flags = set()

        if match.lastindex and match.lastindex >= 2 and match.group(2):
            flags = {f.strip().upper() for f in match.group(2).split("|")}

        # Normalize name by token type
        if kind == "VAR_INLINE":
            norm_name = name.lower()
        elif kind == "SYSTEM":
            norm_name = name.lower()
        else:  # VAR_BLOCK
            norm_name = name

        token = Token(
            kind=kind,
            raw=raw,
            name=norm_name,
            flags=flags,
            index=idx
        )
        tokens.append(token)

        # ---- metadata tracking ----
        if kind == "VAR_INLINE":
            meta = variables.setdefault(norm_name, VariableMeta())
            meta.occurrences += 1
            meta.flags_seen |= flags
            if "DERIVED" in flags:
                meta.is_derived = True

        elif kind == "VAR_BLOCK":
            meta = blocks.setdefault(norm_name, BlockMeta())
            meta.occurrences += 1

        elif kind == "SYSTEM":
            system_vars[norm_name] = system_vars.get(norm_name, 0) + 1

        idx += 1
        pos = match.end()

    return TokenStream(
        tokens=tokens,
        variables=variables,
        blocks=blocks,
        system_vars=system_vars,
    )
