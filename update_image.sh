#!/bin/bash

# Define the path to the local repository
REPO_PATH="$HOME/autonomi.nodes"

# Define the path to the image on your device
IMAGE_PATH="$HOME/average_nodes_over_time.png"

# Navigate to the repository directory
cd $REPO_PATH

# Copy the new image to the repository
cp $IMAGE_PATH $REPO_PATH/average_nodes_over_time.png

# Add only the updated image to the staging area
git add average_nodes_over_time.png

# Commit the change
git commit -m "Auto Update"

# Push the commit to GitHub
git push origin main
