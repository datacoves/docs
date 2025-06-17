# Reset docker config authentication

If that was the case, you might need to log in and log out again after a password reset:

```
docker logout
```

Then, remove the entry for taqy-docker.artifactrepo.jnj.com in `~/.docker/config.json`.

Finally, login again:

```
docker login taqy-docker.artifactrepo.jnj.com
```

# Unlock your artifactory account

Sometimes your account can get blocked and you need to unlock it.

1. Go to [appdevtools](https://appdevtools.jnj.com)
2. Under support, user acces, click on `Unlock Artifactory Account`.
