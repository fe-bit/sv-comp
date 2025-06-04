#!/bin/bash
#SBATCH --job-name=gsoc-eval_strategies_nvembed
#SBATCH -o ./jobs/eval/nvembed/%x.%j.out
#SBATCH -e ./jobs/eval/nvembed/%x.%j.err
#SBATCH -D ./
#SBATCH --time=0:30:00
#SBATCH --partition=NvidiaAll
#SBATCH --cpus-per-task=8
#SBATCH --comment=""

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK
export TORCH_NUM_THREADS=$SLURM_CPUS_PER_TASK
lscpu
amd-smi
source env/bin/activate
python3 manage.py eval_strategy_nvembed
