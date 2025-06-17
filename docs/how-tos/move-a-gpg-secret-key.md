# How to move a gpg secret key

You should not reuse private gpg keys without thinking. However, it is more
convenient to have a single private key for your jnj email that is in all the
git secret keyrings of all the cluster config repos that you have access to.

An easy way to transfer a key to a new installation server is to copy and paste
its base64:

```bash
# From the machine that already has the key:
gpg --list-secret-keys
gpg --export-secret-key youremail@its.jnj.com | base64
# Copy the output.
```

```bash
# From the installation machine:
cat | base64 -d > key.asc
# Paste and hit control D.
gpg --import key.asc
gpg --list-secret-keys
rm key.asc
```
