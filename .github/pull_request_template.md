<!---

Provide a short summary of the purpose of this PR.

-->

## Testing steps:

<!---

Uncomment this section and explain the steps needed to make this PR work.

-->

## Checklist:

<!---

This checklist is mostly useful as a reminder of small things that can easily be

forgotten – it is meant as a helpful tool rather than hoops to jump through.

Put an `x` in all the items that apply, make notes next to any that haven't been

addressed, and remove any items that are not relevant to this PR.

-->

- [ ] [Mandatory] My pull request represents one logical piece of work and my commits are related and look clean.

- [ ] [Mandatory] I ran the integration tests (`./cli.py integration_tests`)

- [ ] I have bumped minor or major version accordingly on `.version.yml` (see [Docs](https://github.com/datacoves/datacoves/blob/main/docs/how-tos/datacoves-versioning.md))

- [ ] I created new 1Password items (`./cli.py sync_secrets`)

- [ ] I have built new docker images on this branch (`./cli.py build_and_push`) so `./cli.py set_release` needs to be run to test it

- [ ] This requires configuration changes on the cluster (please specify configuration changes below)

- [ ] IF there are configuration changes or other changes to the release, please SET the 'special release step' label on this issue!

