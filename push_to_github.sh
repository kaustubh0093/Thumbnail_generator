# Run these commands in your terminal from the project root

# Initialize git if not already done
git init

# Add the remote repository (only if not already added)
git remote add origin https://github.com/kaustubh0093/Thumbnail_generator.git

# Do not track .env file
echo ".env" >> .gitignore

# Add all files except .env
git add .

# Commit your changes
git commit -m "Initial commit: YouTube Thumbnail Generator app"

# Push to GitHub (main branch)
git push -u origin main

# If your push is rejected due to repository rules, try these steps:

# 1. Check for required branch name (often 'master' or 'main')
# 2. Check for required commit signatures or PRs (see repo settings)
# 3. Try pushing to a new branch and create a pull request:

git checkout -b feature/initial-upload
git add .
git commit -m "Initial commit: YouTube Thumbnail Generator app"
git push -u origin feature/initial-upload

# Then, go to GitHub and create a pull request from 'feature/initial-upload' to 'main'.
