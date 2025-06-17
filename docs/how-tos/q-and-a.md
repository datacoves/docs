## Questions and Answers

These are simple items that don't necessarily fit in elsewhere or need their own articles.

### How do I start codeserver without validating the git repository credentials?

Code servers use User Repository settings, and currently User Repositories only work with SSH keys.  Sometimes, this is hard to deal with; if we can only use https authentication (i.e. from within J&J pulling an external repository) and we need a work-around.

The workaround is simple; go to the Django panel.

Pick User Repositories

Pick the correct User Repository for your user and repo.

Put a date and time in the "validated at" field and save it.  So long as that isn't blank, it will allow you to start code server.
