# Statement of Purpose

The purpose of this document is to describe the process of upgrading SSL certificates for customers that are using custom certificates (i.e. not using Let's Encrypt).

# Step 1: Prepare and Verify Certificate Files

*This should be done soon after certificate files are received, and not last minute.*

Ultimately, we need the following files:

 * root.cer
 * root.secret.key
 * wildcard.cer
 * wildcard.secret.key

The root.cer is the certificate for the root domain, i.e. datacoves.orrum.com

wildcard.cer is a wildcard, i.e. *.datacoves.orrum.com

All of these files should be in pem format; the cer files should have the complete keychain.  A pem format looks like this:

```
-----BEGIN CERTIFICATE-----
MIIEjTCCAvWgAwIBAgIQQ71EG0d4110tqpc8I8ur/jANBgkqhkiG9w0BAQsFADCB
pzEeMBwGA1UEChMVbWtjZXJ0IGRldmVsb3BtZW50IENBMT4wPAYDVQQLDDVzc2Fz
c2lAU2ViYXN0aWFucy1NYWNCb29rLVByby5sb2NhbCAoU2ViYXN0aWFuIFNhc3Np
....
JbszQlyzkyzBxQ5eiK3OUNdsB+n5Zo+TshRRL45wA9fZmvAizzmtehxJWUbidGL7
eqqMWqdt11MTLJ3feOjGlryMFO6TIt/aH/91VkoLyVhsemuk5LukZ1nIxoWvzHcf
y2cC+I3F8bWbYkRr92fmb8A=
-----END CERTIFICATE-----
```

There should be several BEGIN / END certificate blocks in wildcard.cer and root.cer file; the wildcard.csr and root.csr files should have a complete certificate stack and should be suspect if they only contain a single certificate block.

The key files will have a slightly different header, looking like this:

```
-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCLf9Q17CQlOWDB
CwWOuzL4+aalFwj2PR+OTuPnjHCI8stDedvmy5jtxSkdAL+5PgNu7ZJbKFhbODgT
...
OpuSfWnGVhOmii2aiYePtvNqDsLQv59MUxpUi8R6aw/XhG2Vb7t14+hbmUtRScUV
LcGdNBdJyB8NaHYR/sNF1w==
-----END PRIVATE KEY-----
```

*If you receive a pfx format file, we cover that in a section below.  Read that section and go through those steps, then return to this section to complete verification.*

You can verify the certs with the following commands:

```shell
# Verify root
openssl crl2pkcs7 -nocrl -certfile root.cer | openssl pkcs7 -print_certs -noout -text

# Verify wildcard
openssl crl2pkcs7 -nocrl -certfile wildcard.cer | openssl pkcs7 -print_certs -noout -text
```

And you will see several blocks with a Certificate header.  One block should contain the host name for the certificate.  In our example, datacoves.orrum.com:

```
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            01:cb:00:21:05:34:94:76:2b:f8:68:cf:8a:09:4c:02
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=US, O=DigiCert Inc, OU=www.digicert.com, CN=Thawte TLS RSA CA G1
        Validity
            Not Before: Apr 22 00:00:00 2024 GMT
            Not After : Apr 21 23:59:59 2025 GMT
        Subject: CN=datacoves.orrum.com
```

Note the hostname under 'Subject'; make sure that is the correct host.  root will appear as above, as a single host name; wildcard should look like this instead:

```
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            0d:7f:e3:36:2c:db:b0:65:78:9a:c1:88:f8:06:12:4f
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=US, O=DigiCert Inc, OU=www.digicert.com, CN=Thawte TLS RSA CA G1
        Validity
            Not Before: Apr 22 00:00:00 2024 GMT
            Not After : Apr 21 23:59:59 2025 GMT
        Subject: CN=*.datacoves.orrum.com
```

Note the * symbol there in the subject.  Also take note of the issuer; `CN=Thawte TLS RSA CA G1`.

Elsewhere in the certificate output, you should see a certificate for the issuer, such as:

```
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            09:0e:e8:c5:de:5b:fa:62:d2:ae:2f:f7:09:7c:48:57
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=US, O=DigiCert Inc, OU=www.digicert.com, CN=DigiCert Global Root G2
        Validity
            Not Before: Nov  2 12:24:25 2017 GMT
            Not After : Nov  2 12:24:25 2027 GMT
        Subject: C=US, O=DigiCert Inc, OU=www.digicert.com, CN=Thawte TLS RSA CA G1
```

Note the subject matches the issuer name.  And finally, this certificate has an issuer as well; make sure that one is in the file.  In this case, `DigiCert Global Root G2`.  In our example, you can find it here:

```
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            03:3a:f1:e6:a7:11:a9:a0:bb:28:64:b1:1d:09:fa:e5
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=US, O=DigiCert Inc, OU=www.digicert.com, CN=DigiCert Global Root G2
        Validity
            Not Before: Aug  1 12:00:00 2013 GMT
            Not After : Jan 15 12:00:00 2038 GMT
        Subject: C=US, O=DigiCert Inc, OU=www.digicert.com, CN=DigiCert Global Root G2
```

Note again the 'subject' line.  Typically PEM files will have certificates in the following order:

 * Host's certificate
 * One or More Intermediate
 * Root certificate

If you have to assemble a certificate from multiple parts, please be aware that this is the recommended ordering; however I don't think it will cause an error if you get the ordering wrong.

Once your certificates are in order, you can verify the key with the following commands:

```
openssl rsa -check -noout -in wildcard.secret.key
openssl rsa -check -noout -in root.secret.key
```

Both should say: `RSA key is okay`

Now compare the modulus of the key and the cert:

```
# These two should match
openssl rsa -modulus -noout -in wildcard.secret.key | openssl md5
openssl x509 -modulus -noout -in wildcard.cer | openssl md5

# And these two should match
openssl rsa -modulus -noout -in root.secret.key | openssl md5
openssl x509 -modulus -noout -in root.cer | openssl md5
```

If the modulus doesn't match, it may be because the server certificate isn't the first certificate in the .cer file.  Make sure the order is correct and try again.

## Converting pfx format files

We have received files in pfx format instead of pem and these require special handling.  Follow the following directions to convert them to usable cer and key files, then use the following commands:

```shell
# Assuming we have files wildcard.pfx and root.pfx
#
# Note: The --legacy option seems to be needed for most people, however
#       some are able to do this without --legacy ... you can try without
#       it first if you want.
#
# You will be asked for an "Import Password" -- just hit enter to skip that
# If you get an error after the Import Password, you need --legacy

openssl pkcs12 -in wildcard.pfx -cacerts -out wildcard_ca.cer -nodes -nokeys --legacy
openssl pkcs12 -in root.pfx -cacerts -out root_ca.cer -nodes -nokeys --legacy
```

Edit the wildcard.cer and root.cer files, and remove the header above `-----BEGIN CERTIFICATE-----`.  This header will resemble this:

```
Bag Attributes: <No Attributes>
subject=C=US, O=DigiCert Inc, OU=www.digicert.com, CN=Thawte TLS RSA CA G1
issuer=C=US, O=DigiCert Inc, OU=www.digicert.com, CN=DigiCert Global Root G2
```

*WARNING: Check the ENTIRE file, as there will probably be multiple of the headers.  Any text not between `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` must be removed!*

Next, you need to extract the server certs, thusly:

```
# See notes above regarding --legacy and "Import Password"

openssl pkcs12 -in wildcard.pfx -clcerts -nokeys -out wildcard.single.cer --legacy
openssl pkcs12 -in root.pfx -clcerts -nokeys -out wildcard.single.cer --legacy
```

Once again, delete the header(s) above `-----BEGIN CERTIFICATE-----` in these files.  Afterwards, run the following command:

```
cat wildcard.single.cer wildcard_ca.cer > wildcard.cer
cat root.single.cer root_ca.cer > root.cer
```

Now we're going to generate the private keys.  When generating the private keys, set a temporary password (just the word `password` is fine); we will remove the password in the subsequent step.

```
# See notes above regarding --legacy and "Import Password"
openssl pkcs12 -in wildcard.pfx -nocerts -out wildcard.secrets.withpass.key --legacy
openssl pkcs12 -in root.pfx -nocerts -out root.secrets.withpass.key --legacy
```

And finally, strip the passwords out for the final key files:

```
openssl rsa -in wildcard.secrets.withpass.key -out wildcard.secret.key
openssl rsa -in root.secrets.withpass.key -out root.secret.key
```

Now you have the files in PEM format, and you can go back to the section above to verify them.

# Step 2: Update Cluster

This step may vary from customer to customer, so see the appropriate subsection.

## Orrum

First, make sure you have the configuration repository checked out.  In your `config` directory, clone it thusly:

```
git clone https://github.com/datacoves/config-datacoves-orrum.git datacoves.orrum.com
```

In the `datacoves.orrum.com` directory, reveal the secrets.  If you call this command within a sub directory, you'll get an error about `core-api.env.secret` cannot be found.

```
git secret reveal -f
```

TODO: add instructions for setting up git secret

Then in the `base` directory you will find `root.cer`, `root.secret.key`, `wildcard.cer`, and `wildcard.secret.key`.  Replace these files with the new, verified files from step 1.

Connect to the Orrum VPN.  Instructions are here: https://github.com/datacoves/datacoves/tree/main/docs/client-docs/orrum

Make sure you are in your Orrum context, whatever that is named:

```
# Use:
# kubectl config get-contexts
# To get context list if needed.
kubectl config use-context orrum_new
```

Then run setup base.  Return to the root directory of your git checkout to run `cli.py` thusly:

```
# Activate your venv first if necessary
./cli.py setup_base
```

After the cluster is updated (ingress will be updated), check the certificate:

```
curl https://api.datacoves.orrum.com -vI
```

This should output a bunch of information about the certificate, including:

```
* Server certificate:
*  subject: CN=*.datacoves.orrum.com
*  start date: Apr  8 07:33:48 2024 GMT
*  expire date: Jul  1 07:33:47 2024 GMT
*  subjectAltName: host "api.datacoves.orrum.com" matched cert's "*.datacoves.orrum.com"
*  issuer: C=US; O=DigiCert Inc; OU=www.digicert.com; CN=Thawte TLS RSA CA G1
*  SSL certificate verify ok.
```

(The CN should be the correct host, and the expire date should be correct).

Check the non-wildcard version as well:

```
curl https://datacoves.orrum.com -vI
```

Log into Orrum's launchpad and go into one of the environments to make sure pomerium doesn't have any issues; pomerium is particularly sensitive to certificate problems such as not having the full certificate chain in the root.cer / wildcard.cer files.

If everything works alright, let's push the secrets.  Be careful to not push up the key files as they will show up as "Untracked Files" in a `git status`.  It is recommended you manually add the files thusly:

```
# Go back to the config directory
cd config/datacoves.orrum.com

# See what files changed
git status

# Add only the changed files, do NOT add the .key files or the original .pfx
git add .gitsecret/paths/mapping.cfg base/root.cer base/wildcard.cer secrets/core-api.env.secret secrets/docker-config.secret.json.secret secrets/rabbitmq.env.secert

# You can also add any other safe file that you modified, just not those keys!

git commit -m "Update certificates"
git push
```

And it should be done!
