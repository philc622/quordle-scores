#!/bin/bash

set -e  # Exit on any error

echo "Check for any quordle emails older than 30 days and delete them"

source ~/.env

source ~/quordle-scores/env/bin/activate

python ~/scripts/delete_old_quordle_emails.py --dry-run False --days 30

echo "Done!"
