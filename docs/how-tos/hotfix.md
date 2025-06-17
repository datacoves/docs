## How to Create a Hotfix

A hotfix is defined as doing a targetted fix to an existing release.  The idea behind a hotfix is to do the absolute minimum change to correct a high priority issue in a live release.

To create a hotfix, one must first do the fix.  First, create a branch from the release tag you wish to hot fix.  Let's say you're hot-fixing release 'TAG_NAME'.  You would do the following commands:

```
git fetch --all --tags
git checkout -b BRANCH_NAME refs/tags/TAG_NAME
```

You will now have a branch that is a copy of the release tag.  You can either do your hotfix work directly on that branch and merge it to main later, or you can use `git cherry-pick` to pick commits from the main branch onto your new branch.  If you need to use cherrypick and you don't know how, that is a larger topic than I want to cover here; Stephen can help you directly with that.

Once you have done your work, you should **commit** to your branch and then compare your branch to the original tag.  This will make sure you only changed what was needed:

```
git diff BRANCH_NAME..refs/tags/TAG_NAME
```

This command **is very important if you cherry-pick** to make sure you don't accidentally bring additional features or code that you do not intend to.  However, it is good practice to review all code going into a hotfix very carefully.

Once you are certain your hotfix is good, **push** it to the git repository.  Now you're ready to build a hotfix release with cli.py.  Do the following command:

```
./cli.py generate_hotfix
```

It will first show you `git status` to make sure your code is committed.  Make sure there are no extra files or anything you don't want built into the release docker image present in your code tree.

After you confirm, it will ask you which release you are making a hotfix from.  This release must already be present in your `releases/` directory; if it is not, download the release with `./cli.py download_releases` or download the appropriate manifest directly from github.

Then, it will ask you which images you wish to build.  Select one or more images to build, or none if you are changing another dependency.

After that, it will ask you if you want to change the version of any other image that is in the release.  You can select none if you only want to build new images and you don't need to change any other dependencies.

Finally, it will build your release and push it up as a draft in github.  From that point, it is a normal release and you can take it through the normal process to get it installed.
