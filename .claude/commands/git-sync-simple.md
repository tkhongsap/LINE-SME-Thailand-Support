---
description: Simple git sync - pull main, fetch prune, and clean up gone branches
allowed-tools: ["Bash"]
---

# Simple Git Sync

Synchronize your local repository with remote main branch.

## Step 1: Switch to main and pull latest

!git checkout main && git pull origin main

## Step 2: Fetch and prune remote references

!git fetch --prune

## Step 3: Clean up local branches that are gone from remote

!git branch -vv | grep ': gone]' | awk '{print $1}' | xargs -r git branch -d

## Step 4: Show final status

!echo "=== Git sync complete! ==="
!echo "Current branch:" && git branch --show-current
!echo ""
!echo "All branches:" && git branch -vv