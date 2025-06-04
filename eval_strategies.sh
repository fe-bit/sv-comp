#!/bin/bash
#SBATCH --job-name=gsoc-eval_strategies
#SBATCH -o ./jobs/eval/transformer/%x.%j.out
#SBATCH -e ./jobs/eval/transformer/%x.%j.err
#SBATCH -D ./
#SBATCH --time=2:30:00
#SBATCH --partition=NvidiaAll
#SBATCH --comment=""

source env/bin/activate
python3 manage.py eval_strategy
