#!/bin/bash
#SBATCH --job-name=gsoc-eval_strategies
#SBATCH -o ./jobs/eval/transformer/%x.%j.out
#SBATCH -e ./jobs/eval/transformer/%x.%j.err
#SBATCH -D ./
#SBATCH --time=2:30:00
#SBATCH --partition=NvidiaAll
#SBATCH --cpus-per-task=8
#SBATCH --comment=""

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK
export TORCH_NUM_THREADS=$SLURM_CPUS_PER_TASK

source env/bin/activate
python3 manage.py eval_strategy
