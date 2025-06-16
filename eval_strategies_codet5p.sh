#!/bin/bash
#SBATCH --job-name=gsoc-eval_strategies_codet5p
#SBATCH -o ./jobs/eval/codet5p/%x.%j.out
#SBATCH -e ./jobs/eval/codet5p/%x.%j.err
#SBATCH -D ./
#SBATCH --time=10:30:00
#SBATCH --partition=AMD
#SBATCH --comment=""

export OMP_NUM_THREADS=1
export SLURM_CPUS_PER_TASK=1
source env/bin/activate
python3 manage.py eval_strategy_codet5p
