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
