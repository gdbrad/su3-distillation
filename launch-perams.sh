#!/bin/bash

# Check if required arguments are provided
if [ $# -lt 4 ]; then
  echo "Usage: $0 <basedir> <cfg_i> <cfg_f> <cfg_step>"
  exit 1
fi

BASEDIR="$1"
CFG_I="$2"
CFG_F="$3"
CFG_STEP="$4"

# Validate base directory
if [ ! -d "$BASEDIR" ]; then
  echo "Error: $BASEDIR is not a valid directory"
  exit 1
fi

# Validate numeric inputs
if ! [[ "$CFG_I" =~ ^[0-9]+$ ]] || ! [[ "$CFG_F" =~ ^[0-9]+$ ]] || ! [[ "$CFG_STEP" =~ ^[0-9]+$ ]]; then
  echo "Error: cfg_i, cfg_f, and cfg_step must be positive integers"
  exit 1
fi

if [ "$CFG_I" -gt "$CFG_F" ]; then
  echo "Error: cfg_i must be less than or equal to cfg_f"
  exit 1
fi

if [ "$CFG_STEP" -eq 0 ]; then
  echo "Error: cfg_step cannot be zero"
  exit 1
fi

# Process configuration directories within the specified range
found=false
for ((i=CFG_I; i<=CFG_F; i+=CFG_STEP)); do
  cfg_dir="$BASEDIR/ini-perams/cnfg$i"
  if [ -d "$cfg_dir" ]; then
    found=true
    cd "$cfg_dir" || continue

    echo "Processing directory $cfg_dir"

    # Find and execute all .sh scripts in the current cfg_dir
    for script in *.sh; do
      if [ -f "$script" ]; then
        echo "Running $script..."
        sbatch "$script" || echo "Error running $script"
      else
        echo "No shell scripts found in $cfg_dir"
        break
      fi
    done

    cd - > /dev/null
  fi
done

if [ "$found" = false ]; then
  echo "No valid configuration directories found in $BASEDIR for the specified range"
fi
