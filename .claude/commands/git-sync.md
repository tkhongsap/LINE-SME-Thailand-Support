---
description: Synchronize git repository with remote - pull main, fetch with prune, and clean up local branches
allowed-tools: ["Bash"]
---

# Git Repository Synchronization

This command performs a comprehensive git repository synchronization:
1. Pulls the latest changes from origin/main
2. Fetches all remote references with pruning
3. Cleans up local branches that no longer exist on remote

## Step 1: Store current branch and switch to main

!git rev-parse --abbrev-ref HEAD > /tmp/current_branch.txt
!echo "Current branch: $(cat /tmp/current_branch.txt)"

!if [ "$(cat /tmp/current_branch.txt)" != "main" ]; then
  echo "Switching to main branch..."
  git checkout main
else
  echo "Already on main branch"
fi

## Step 2: Pull latest changes from origin/main

!echo "Pulling latest changes from origin/main..."
!git pull origin main

## Step 3: Fetch all remotes with prune

!echo "Fetching all remotes and pruning deleted branches..."
!git fetch --prune

## Step 4: Clean up local branches that no longer exist on remote

!echo "Identifying local branches to clean up..."

# Get list of remote branches (excluding HEAD pointer)
!git branch -r | grep -v '/HEAD' | sed 's/origin\///' > /tmp/remote_branches.txt

# Get list of local branches (excluding current branch)
!git branch | grep -v '^\*' | sed 's/^[ \t]*//' > /tmp/local_branches.txt

# Find local branches that don't exist on remote (excluding main)
!comm -23 <(sort /tmp/local_branches.txt) <(sort /tmp/remote_branches.txt) | grep -v '^main$' > /tmp/branches_to_delete.txt

!if [ -s /tmp/branches_to_delete.txt ]; then
  echo "Local branches to be deleted:"
  cat /tmp/branches_to_delete.txt
  echo ""
  echo "Deleting local branches that no longer exist on remote..."
  while IFS= read -r branch; do
    if [ -n "$branch" ]; then
      echo "Deleting branch: $branch"
      git branch -D "$branch" 2>/dev/null || echo "Failed to delete $branch (may be partially merged)"
    fi
  done < /tmp/branches_to_delete.txt
else
  echo "No local branches need to be cleaned up."
fi

## Step 5: Return to original branch (if it still exists)

!original_branch=$(cat /tmp/current_branch.txt)
!if [ "$original_branch" != "main" ]; then
  if git show-ref --verify --quiet "refs/heads/$original_branch"; then
    echo "Returning to original branch: $original_branch"
    git checkout "$original_branch"
  else
    echo "Original branch '$original_branch' no longer exists. Staying on main."
  fi
fi

## Step 6: Clean up temporary files

!rm -f /tmp/current_branch.txt /tmp/remote_branches.txt /tmp/local_branches.txt /tmp/branches_to_delete.txt

## Summary

!echo ""
!echo "Git synchronization complete!"
!echo "Current status:"
!git status --porcelain | wc -l | xargs echo "Uncommitted changes:"
!git branch -v