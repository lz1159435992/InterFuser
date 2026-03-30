import json
from pathlib import Path

# Resolve repo root from this script location to avoid machine-specific absolute paths.
ROOT = Path(__file__).resolve().parents[3]
BASE_FILES = {
    "Town05": ROOT / "output" / "interfuser" / "interfuser_town05_result.json",
    "42 Routes": ROOT / "output" / "interfuser" / "interfuser_42routes_result.json",
}
NATIVE_DIR = ROOT / "output" / "interfuser" / "native"


def load_route_ids(path: Path) -> set[str]:
    obj = json.load(path.open("r", encoding="utf-8"))
    recs = obj.get("_checkpoint", {}).get("records", [])
    out: set[str] = set()
    for r in recs:
        if isinstance(r, dict):
            rid = r.get("route_id")
            if isinstance(rid, str) and rid:
                out.add(rid)
    return out


def main() -> int:
    base_ids = {suite: load_route_ids(p) for suite, p in BASE_FILES.items()}
    print("# baseline route counts")
    for suite in ("Town05", "42 Routes"):
        print(f"{suite}\t{len(base_ids[suite])}")

    print("\n# native alignment")
    for p in sorted(NATIVE_DIR.glob("*.json")):
        name = p.stem
        if name.startswith("town05_"):
            suite = "Town05"
        elif name.startswith("42routes_"):
            suite = "42 Routes"
        else:
            continue

        ids = load_route_ids(p)
        inter = len(ids & base_ids[suite])
        missing = len(base_ids[suite] - ids)
        extra = len(ids - base_ids[suite])
        ok = (missing == 0 and extra == 0)
        print(
            f"{suite}\t{name}\tn={len(ids)}\tinter={inter}\tmissing={missing}\textra={extra}\tOK={ok}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
