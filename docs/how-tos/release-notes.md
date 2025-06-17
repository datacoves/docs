# Statement of Purpose

The purpose of this document is to describe the process by which we manage release notes to deliver to our customers.

# Source of Authority

Release notes all come from Github:

https://github.com/datacoves/datacoves/releases

The notes begin live as auto-generated notes that are created when the release branch is built.  Then, we hand-edit the release notes to match the following format:

```
Breaking Changes
* Items that are breaking changes, in list.

New Features
* New features, in list.

Enhancements
* Enhancements to old features, in list

Fixes
* Bug fixes, in list

Under the Hood
* Notes relevant to us internally which we would like to keep, but not important to customers.

**Full Changelog**: This is a URL that is provided automatically, just leave it in the change log.
```

# Generating Release Notes

Release notes are generated per-customer and have all the changes from their current release to the latest release you currently have downloaded in your 'releases' folder.  Make sure you have the customer's cluster configuration checked out into your 'config' directory; if you do not, stop and ask for help before continuing.

You can control which release notes are generated; make sure you have downloaded the releases first:

```
./cli.py download_releases
```

If desired or necessary, you can delete files out of your 'releases' directory; for instance, if the customer is getting updated to the latest 2.2 series release but there are 2.3 series releases available, you could delete all the 2.3 release files out of your 'releases' directory and notes for those releases will not be produced.

Release notes are then generated using the `cli.py` thusly:

```
./cli.py combined_release_notes
```

It will make a file `combined.md` in the same directory as `cli.py`, and that will have the combined release notes for all the releases involved.  This file can then be delivered to the customer as part of the announcement to upgrade them.
