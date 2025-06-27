#!/bin/bash

# Push to GitHub - Run this after creating the repository on GitHub

echo "Setting up GitHub remote and pushing..."

# Replace 'yourusername' with your actual GitHub username
GITHUB_USERNAME="yourusername"
REPO_NAME="wattzo-bespaarplan-agent"

# Add the remote
git remote add origin "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

# Verify remote was added
echo "Remote added:"
git remote -v

# Push all branches and tags
echo "Pushing to GitHub..."
git push -u origin main

echo "Done! Your repository is now on GitHub at:"
echo "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"