# Getting Started with Git - Branches and Changes

This guide covers essential Git commands for managing branches and making changes in your Git repository.

## Managing Branches

- **View Current Branch:** Check the current branch in your Git repository.

- **View All Branches Locally and Remote:** See both local and remote branches in your repository.

- **View local branches - `git branch`:** List all local branches using the `git branch` command.

- **Create a new branch - `git checkout -b <new_branch> <reference_branch>`:** Create a new branch and switch to it with a single command.

- **Switch branches - `git checkout <branch-name>`:** Allows you to navigate between branches or commits, restore files, and create new branches.
  
- **Switch branches (cont) - `git switch <branch-name>`:** A simpler command to switch between branches.

- **Stash changes - `git stash`:** Temporarily save your changes without committing them.

## Managing Changes

- **Open Modified Files:** View files with changes that haven't been committed.

- **View Side-by-Side Changes:** Compare changes between two versions side by side.

- **View Inline Changes:** View changes inline within the code.

- **Discard Changes:** Undo modifications and revert to the last committed state.

- **Stage Changes:** Prepare changes for a commit by staging them.

- **Commit:** Save staged changes with a commit message.

- **Undo Commit:** Undo the last commit while keeping changes in your working directory.

## Aliased Commands

- **git br = git branch:** Use `git br` to see available branches.

- **git co = git checkout:** Quickly switch to another branch with `git co`.

- **git l = git log:** View the commit log with `git l`.

- **git st = git status:** Check the Git status of your repository using `git st`.

- **git po:** Pull changes from the main branch into your local branch (specific usage may vary).

- **git prune-branches:** Delete local branches that have been deleted on the remote server.

For more in-depth information and advanced usage, please consult the **[Source Control Extension Docs](https://code.visualstudio.com/docs/sourcecontrol/overview)**.

<div style="position: relative; padding-bottom: 56.25%; height: 0;"><iframe src="https://www.loom.com/embed/67ea31eef4d94a5e844a5393684e4bc6?sid=f52c0561-ceb5-4baf-ba06-ab739ef3fcc5" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

## Resources

- [Git Documentation](https://git-scm.com/doc)
- [How Git Works](https://www.youtube.com/watch?v=e9lnsKot_SQ)
- [GitHub Learning Lab](https://github.com/apps/github-learning-lab)
- [Git Cheat Sheet](https://github.com/github/training-kit/blob/master/downloads/github-git-cheat-sheet.pdf)
- [Git rebase - Why, When & How to fix conflicts ](https://youtube.com/watch?v=DkWDHzmMvyg&si=WE4VeEY1HKa_ejEA)
- [Git merge/pull tutorial](https://youtube.com/watch?v=DloR0BOGNU0&si=3EfopCU41XvkYkJJ)
- [Git pull rebase](https://youtube.com/watch?v=xN1-2p06Urc&si=8ZGMhJSy-A6N62l6)
