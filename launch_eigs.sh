#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <basedir>"
  exit 1
fi

BASEDIR="$1"

if [ ! -d "$BASEDIR" ]; then
  echo "Error: $BASEDIR is not a valid directory"
  exit 1
fi

for cfg_dir in "$BASEDIR"/ini-eigs/cnfg*/; do
  if [ -d "$cfg_dir" ]; then
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
  else
    echo "No valid configuration directories found in $BASEDIR"
    break
  fi
done