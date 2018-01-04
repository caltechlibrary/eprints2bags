#!/bin/bash

# Operates on the current directory.
# MAKE SURE YOU ARE IN THE CORRECT DIRECTORY BEFORE RUNNING THIS!!!

# For each directory in the current directory,
# bag the contents, then tar and gzip the bag.
 
for dir in */
do
  echo "Bagging $dir..."
  /opt/bagit-python/bagit.py $dir 
  base=$(basename "$dir")
  echo "Tar/gzipping $dir..."
  tar -czf "${base}.tgz" "$dir"
  echo "File ${base}.tgz created..."
  echo "Removing original directory $dir..."
  rm -Rf $dir
done
 
