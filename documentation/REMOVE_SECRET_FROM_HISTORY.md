# How to Remove Secret from Git History

The API key is in commit `a6bd2c69f0aec849fb8a5a3ab1bd7de9799cb3ff`. We need to remove it from history.

## Option 1: Interactive Rebase (Recommended for small history)

```bash
# Find the commit with the secret
git log --oneline | grep a6bd2c69

# Start interactive rebase from before that commit
git rebase -i a6bd2c69^  # ^ means "parent of"

# In the editor, change "pick" to "edit" for commit a6bd2c69
# Save and close

# Remove the API key from the file (already done, but verify)
# Then:
git add backend/data/workflows/a118eef6-45e8-4a0a-888d-3e6e61452b0c.json
git commit --amend --no-edit
git rebase --continue

# Force push (since we rewrote history)
git push origin ui --force
```

## Option 2: Remove file from all commits (Easier)

Since user workflows shouldn't be in git anyway:

```bash
# Remove the file from all commits in history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/data/workflows/a118eef6-45e8-4a0a-888d-3e6e61452b0c.json" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin ui --force
```

## Option 3: Use BFG Repo-Cleaner (Fastest, but requires Java)

```bash
# Install BFG (if not installed)
# Download from: https://rtyley.github.io/bfg-repo-cleaner/

# Remove the file
bfg --delete-files a118eef6-45e8-4a0a-888d-3e6e61452b0c.json

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin ui --force
```

## Option 4: Start Fresh Branch (If history is not critical)

```bash
# Create new branch from main/master without the problematic commits
git checkout main
git checkout -b ui-clean
git cherry-pick <commit-after-secret>  # Pick commits after the secret

# Or reset to before the secret commit
git reset --hard <commit-before-secret>
git push origin ui-clean --force
```

## ⚠️ Important Notes

1. **Force push rewrites history** - coordinate with team if others have pulled
2. **The secret is already exposed** - rotate the API key immediately
3. **User workflows should never be in git** - only templates should be committed

## Recommended: Remove ALL user workflows from git

Since user workflows are UUID-based and shouldn't be in git:

```bash
# Remove all user workflow files from git (keep templates)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/data/workflows/*.json" \
  --prune-empty --tag-name-filter cat -- --all

# Then add templates back
git checkout main -- backend/data/workflows/*-template.json
git commit -m "Keep only template workflows in git"

# Force push
git push origin ui --force
```

