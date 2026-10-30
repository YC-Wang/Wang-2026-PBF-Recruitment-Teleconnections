"""Verify configured observational inputs without changing or executing science."""
from __future__ import annotations
import argparse, hashlib, os
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility
    try: import tomli as tomllib
    except ModuleNotFoundError: tomllib = None
import ast
from pathlib import Path

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()

def load_config(path: Path) -> dict:
    if tomllib is None:
        result = {}; section = result
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line: continue
            if line.startswith("[") and line.endswith("]"):
                section = result.setdefault(line[1:-1], {})
            else:
                key, value = line.split("=", 1); value = value.strip()
                try: parsed = ast.literal_eval(value)
                except (ValueError, SyntaxError): parsed = value.strip('"')
                section[key.strip()] = parsed
        return result
    with path.open("rb") as stream: return tomllib.load(stream)

def resolve(root: Path, value: str) -> Path:
    if value.startswith("repo/"): return root / value.removeprefix("repo/")
    return Path(os.environ.get("PBF_DATA_ROOT", root)) / value

def verify(config_path: Path, repo_root: Path, include_tracked: bool = False) -> int:
    config = load_config(config_path); failures = []
    for name, relative in config["inputs"].items():
        path = resolve(repo_root, relative); expected = config["sha256"].get(name)
        if not path.is_file(): failures.append(f"MISSING {name}: {path}"); continue
        actual = sha256(path)
        if expected and actual != expected: failures.append(f"CHECKSUM {name}: expected {expected}, found {actual}")
        else: print(f"OK {name}: {path} ({actual})")
    if include_tracked:
        for name, relative in config["tracked_inputs"].items():
            path = resolve(repo_root, relative)
            if not path.exists(): failures.append(f"MISSING tracked {name}: {path}")
            else: print(f"OK tracked {name}: {path}")
    for failure in failures: print(f"ERROR {failure}")
    return 1 if failures else 0

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, default=Path("configs/observational_paths.toml")); parser.add_argument("--repo-root", type=Path, default=Path.cwd()); parser.add_argument("--include-tracked", action="store_true")
    args = parser.parse_args(); return verify(args.config.resolve(), args.repo_root.resolve(), args.include_tracked)

if __name__ == "__main__": raise SystemExit(main())
