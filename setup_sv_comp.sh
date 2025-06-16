#!/bin/bash
#SBATCH --job-name=gsoc-setup_sv_comp
#SBATCH -o ./jobs/%x.%j.out
#SBATCH -e ./jobs/%x.%j.err
#SBATCH -D ./
#SBATCH --time=00:15:00
#SBATCH --partition=AMD
#SBATCH --comment=""

source env/bin/activate
python3 manage.py setup_sv_comp
