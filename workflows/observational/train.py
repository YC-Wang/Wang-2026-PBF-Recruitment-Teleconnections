import argparse
from src.pbf.observational import run_training

def main():
    parser = argparse.ArgumentParser(description="Train fold-specific observational GAM/RF models; no held-out skill is calculated.")
    parser.add_argument("--svd-csv", required=True); parser.add_argument("--recruitment-csv", required=True); parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(); run_training(args.svd_csv, args.recruitment_csv, args.output_dir)

if __name__ == "__main__": main()
