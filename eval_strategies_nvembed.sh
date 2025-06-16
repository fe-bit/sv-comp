#!/bin/bash
#SBATCH --job-name=gsoc-eval_strategies_nvembed
#SBATCH -o ./jobs/eval/nvembed/%x.%j.out
#SBATCH -e ./jobs/eval/nvembed/%x.%j.err
#SBATCH -D ./
#SBATCH --time=16:30:00
#SBATCH --partition=AMD
#SBATCH --comment=""


lscpu
amd-smi static -g 0
source env/bin/activate
python3 manage.py eval_strategy_nvembed
