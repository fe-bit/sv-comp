#!/bin/bash
# sbatch train_verifier_predict.sh
#SBATCH --job-name=TrainVerifierPredict
#SBATCH -o ./jobs/%x.%j.out
#SBATCH -e ./jobs/%x.%j.err
#SBATCH -D ./
#SBATCH --time=05:15:00
#SBATCH --partition=AMD
#SBATCH --comment=""

source env/bin/activate
python3 train_verifier_predict.py
