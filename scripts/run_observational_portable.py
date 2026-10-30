"""Config-driven Level 2 entry point delegating to the unchanged trainer."""
from __future__ import annotations
import argparse
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility
    import tomli as tomllib
from pathlib import Path
from scripts.verify_observational_inputs import resolve, verify
from src.pbf.observational import run_training

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, default=Path("configs/observational_paths.toml")); parser.add_argument("--repo-root", type=Path, default=Path.cwd()); parser.add_argument("--output-dir", type=Path, required=True); parser.add_argument("--skip-input-verification", action="store_true")
    args = parser.parse_args(); config_path=args.config.resolve(); repo_root=args.repo_root.resolve()
    with config_path.open("rb") as stream: config=tomllib.load(stream)
    if not args.skip_input_verification and verify(config_path, repo_root) != 0: return 2
    run_training(resolve(repo_root, config["inputs"]["fold_predictors"]), resolve(repo_root, config["inputs"]["observed_recruitment"]), args.output_dir.resolve())
    print(f"Wrote isolated Level 2 outputs to {args.output_dir.resolve()}"); return 0

if __name__ == "__main__": raise SystemExit(main())
