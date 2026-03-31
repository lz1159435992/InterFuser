import os
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Sequence, Tuple

import numpy as np

from .augseq_parser import AugmentSeq
from .spatial_pipeline import SpatialPipeline


def _parse_camera_list(value: Optional[str], default: str) -> Tuple[str, ...]:
    v = (value or "").strip()
    if not v:
        v = default
    items = [x.strip() for x in v.split(",")]
    items = [x for x in items if x]
    return tuple(items)


def load_fi_apply_to_from_env(env_key: str = "FI_APPLY_TO") -> Tuple[str, ...]:
    return _parse_camera_list(os.environ.get(env_key), default="rgb,rgb_left,rgb_right")


@dataclass
class AugSeqPipelines:
    augseq: AugmentSeq
    fi_apply_to: Tuple[str, ...]

    no_fi_pipeline: Optional[SpatialPipeline]
    prefix_pipeline: Optional[SpatialPipeline]
    suffix_pipeline: Optional[SpatialPipeline]


def build_pipelines(augseq: AugmentSeq, fi_apply_to: Optional[Sequence[str]] = None) -> AugSeqPipelines:
    fi_apply_to_tuple = tuple(fi_apply_to) if fi_apply_to is not None else load_fi_apply_to_from_env()

    if augseq.fi_index is None:
        no_fi = SpatialPipeline(augseq.ops)
        return AugSeqPipelines(
            augseq=augseq,
            fi_apply_to=fi_apply_to_tuple,
            no_fi_pipeline=no_fi,
            prefix_pipeline=None,
            suffix_pipeline=None,
        )

    prefix = SpatialPipeline(augseq.prefix_ops)
    suffix = SpatialPipeline(augseq.suffix_ops)
    return AugSeqPipelines(
        augseq=augseq,
        fi_apply_to=fi_apply_to_tuple,
        no_fi_pipeline=None,
        prefix_pipeline=prefix,
        suffix_pipeline=suffix,
    )


def apply_pipeline_to_cameras(
    pipeline: SpatialPipeline,
    images_by_id: Dict[str, np.ndarray],
    apply_to: Iterable[str],
) -> Dict[str, np.ndarray]:
    return pipeline.process_cameras(images_by_id=images_by_id, apply_to=apply_to)
