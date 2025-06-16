#!/bin/bash
# sbatch eval_strategies_qwen.sh
#SBATCH --job-name=gsoc-eval_strategies_qwen
#SBATCH -o ./jobs/eval/qwen/%x.%j.out
#SBATCH -e ./jobs/eval/qwen/%x.%j.err
#SBATCH -D ./
#SBATCH --time=10:30:00
#SBATCH --partition=NvidiaAll
#SBATCH --comment=""

source env/bin/activate
python3 manage.py eval_strategy_qwen
