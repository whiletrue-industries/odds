#!/bin/bash
# This script generates TypeScript interfaces from Python datatypes using the python-to-typescript-interfaces tool.
python-to-typescript-interfaces -e \
        -o ./frontend/admin/projects/admin/src/app/datatypes.ts \
        ./odds/common/datatypes.py