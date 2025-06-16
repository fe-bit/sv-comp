#!/bin/bash
#SBATCH --job-name=gsoc-eval_strategies_gemini
#SBATCH -o ./jobs/eval/gemini/%x.%j.out
#SBATCH -e ./jobs/eval/gemini/%x.%j.err
#SBATCH -D ./
#SBATCH --time=1:30:00
#SBATCH --partition=AMD
#SBATCH --comment=""

source env/bin/activate
python3 manage.py eval_strategy_gemini
