#!/bin/bash

torch-model-archiver \
    --model-name sd3 \
    --version 1.0 \
    --handler sd3_handler.py \
    --requirements-file requirements.txt \
    -f \
    --export-path ./model-store

echo "MAR file created at ../model-store/sd3.mar" 