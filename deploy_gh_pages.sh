#!/bin/bash
cd frontend/build
rm -rf .git
cp index.html 404.html
touch .nojekyll
git init
git add .
git commit -m "Deploy to gh-pages"
git remote add origin git@github.com:modulabs/growup.git
git push -f origin master:gh-pages
