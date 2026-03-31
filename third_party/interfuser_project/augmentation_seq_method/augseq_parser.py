import os
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple


_ALLOWED_OPS = {"none", "dn15", "srgan_2x", "fi"}


@dataclass(frozen=True)
class AugmentSeq:
    ops: Tuple[str, ...]
    prefix_ops: Tuple[str, ...]
    suffix_ops: Tuple[str, ...]
    fi_index: Optional[int]


def _normalize_token(tok: str) -> str:
    return tok.strip().lower()


def parse_augment_seq(seq_str: Optional[str]) -> Tuple[str, ...]:
    if seq_str is None:
        return ("none",)

    s = seq_str.strip()
    if not s:
        return ("none",)

    tokens = [_normalize_token(t) for t in s.split(",") if _normalize_token(t)]
    if not tokens:
        return ("none",)

    for t in tokens:
        if t not in _ALLOWED_OPS:
            raise ValueError(f"Unknown AUGMENT_SEQ op: {t}")

    if "none" in tokens and len(tokens) > 1:
        raise ValueError("AUGMENT_SEQ contains 'none' with other ops")

    return tuple(tokens)


def split_prefix_suffix(ops: Sequence[str]) -> Tuple[Tuple[str, ...], Tuple[str, ...], Optional[int]]:
    fi_positions = [i for i, op in enumerate(ops) if op == "fi"]
    if len(fi_positions) == 0:
        return tuple(ops), tuple(), None
    if len(fi_positions) > 1:
        raise ValueError("AUGMENT_SEQ contains multiple 'fi'")

    idx = fi_positions[0]
    prefix = tuple(ops[:idx])
    suffix = tuple(ops[idx + 1 :])
    return prefix, suffix, idx


def load_augseq_from_env(env_key: str = "AUGMENT_SEQ") -> AugmentSeq:
    seq_str = os.environ.get(env_key)
    ops = parse_augment_seq(seq_str)
    prefix, suffix, idx = split_prefix_suffix(ops)
    return AugmentSeq(ops=ops, prefix_ops=prefix, suffix_ops=suffix, fi_index=idx)
