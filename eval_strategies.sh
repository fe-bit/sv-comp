#!/bin/bash
#SBATCH --job-name=gsoc-eval_strategies
#SBATCH -o ./jobs/eval/%x.%j.out
#SBATCH -e ./jobs/eval/%x.%j.err
#SBATCH -D ./
#SBATCH --time=15:30:00
#SBATCH --partition=AMD
#SBATCH --comment=""

source env/bin/activate
python3 manage.py eval_strategy
