#!/bin/bash

set -e  # Exit on any error

echo "Check for any new scores and update the database"

source ~/.env

source ~/quordle-scores/env/bin/activate

# run email-reader-with-sqlite.py
python ~/scripts/email-reader-with-sqlite.py ~/data/quordle_scores.db

python ~/scripts/extract_to_csv.py ~/data/quordle_scores.db ~/data/quordle_scores.csv

cp ~/data/quordle_scores.csv /var/www/html/quordle
mkdir -p /var/www/html/quordle_data
cp ~/data/quordle_scores.csv /var/www/html/quordle-data/quordle_scores.csv

echo "Done!"
