## Make and work on a pre-release locally

Sometimes you need to change images and test them locally without affecting production releases.

To do so:

### Build the image you just changed

```sh
./cli.py build_and_push <path to service>  # i.e. src/core/api
```

You'll need to specify the issue #

This command will build and push a new image prefixing its name with the ticket number your provided.

### Generate the pre-release

Once the image was pushed, you can create a new pre-release to try that image:

```sh
./cli.py generate_release
```

This will create a new release file under /releases and will also be pushed to GitHub releases so other devs can reuse it.

### Set the pre-release on datacoveslocal.com cluster

```sh
./cli.py set_release
```

Select `datacoveslocal.com`.

You might need to undo the file changes before pushing to PR branch.

### Upgrade datacoves in local cluster

```sh
./cli.py install
```

Select `datacoveslocal.com`