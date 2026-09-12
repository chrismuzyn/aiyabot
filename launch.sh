#!/bin/bash
# Default to no /generate (skips torch/transformers/CUDA packages).
# Set USE_GENERATE=true to enable the /generate command.
export USE_GENERATE="${USE_GENERATE:-false}"

python -m venv venv

source ./venv/bin/activate

case "${USE_GENERATE,,}" in
    true|1|t)
        pip install -r requirements.txt
        python core/setup_generate.py
        ;;
    *)
        pip install -r requirements_no_generate.txt
        ;;
esac

python aiya.py
