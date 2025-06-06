#!/bin/bash
#SBATCH --job-name=gsoc-cleanup_chroma
#SBATCH -o ./jobs/others/cleanup_chroma/%x.%j.out
#SBATCH -e ./jobs/others/cleanup_chroma/%x.%j.err
#SBATCH -D ./
#SBATCH --time=1:30:00
#SBATCH --partition=AMD
#SBATCH --comment=""

source env/bin/activate
python3 manage.py remove_content_in_chroma
