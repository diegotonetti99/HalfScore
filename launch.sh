#!/usr/bin/bash
source /var/home/diego/.bashrc
conda activate halfscore
cd "$(dirname "$0")"
python halfscore.py
