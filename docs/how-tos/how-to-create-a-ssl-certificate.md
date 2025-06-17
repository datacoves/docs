# How to create an SSL certificate

1. Install [acme.sh](https://github.com/acmesh-official/acme.sh#1-how-to-install)

2. Configure the [cloudflare API token](https://github.com/acmesh-official/acme.sh/wiki/dnsapi#1-cloudflare-option) (getting `CF_Key` and `CF_Email` from 1Password). 

3. Run:

```shell
# Let's Encrypt issuer
# https://github.com/acmesh-official/acme.sh/wiki/Server
acme.sh --issue --server letsencrypt --dns dns_cf -d <DOMAIN> --debug 2

# then
acme.sh --issue --server letsencrypt --dns dns_cf -d '*.<DOMAIN>' --debug 2
```

4. Get certificate information (Optional)

```shell
openssl x509 -text -noout -in <cert>
```

5. Copy ceftificates

- Use `<DOMAIN>/fullchain.cer` and `<DOMAIN>/<DOMAIN>.key` as the root certificate and private key. Usually copied then to `base/root.cer` and `base/root.key`.
- Also, use `*.<DOMAIN>/fullchain.cer` and `*.<DOMAIN>/<DOMAIN>.key` as the wildcard certificate and private key. Usually copied then to `base/wildcard.cer` and `base/wildcard.key`.
