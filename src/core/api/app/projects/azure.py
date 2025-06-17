"""
Class to handle interfacing with Azure.  In particular, this is how Azure
credentials can be converted to generate OAuth tokens for GIT checkout.
"""

import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

# How many seconds to wait before aborting Azure CLI commands?  This
# needs to be a reasonable number to make sure we're not waiting forever
# for this.
AZURE_SUBPROCESS_TIMEOUT = 45


class AzureDevops:
    def __init__(
        self,
        tenant_id: str,
        app_id: str,
        secret: str = None,
        certificate: str = None,
    ):
        """Initializes AzureDevops class for various operations.

        Either 'secret' or 'certificate' is required.  'secret' will trump
        certificate if both are provided.

        Certificate is the public key with the private key appended.  In
        our objects, this is usually like:

        project_repo.azure_deploy_key.public + "\n" +
        project_repo.azure_deploy_key.private

        """

        self.tenant_id = tenant_id
        self.app_id = app_id

        if secret is not None:
            self.secret = secret
            self.certificate = None
        elif certificate is not None:
            self.secret = None
            self.certificate = certificate
        else:
            raise RuntimeError("secret or certificate must be provided")

        # This is used in a few places and is properly configured by
        # _login
        self.env_dict = dict(os.environ)

    def _redact_exception(self, e: subprocess.CalledProcessError):
        """Redacts a CalledProcessError exception to clean out potential
        secrets.
        """

        for i in range(0, len(e.cmd)):
            if e.cmd[i] in (self.app_id, self.secret, self.tenant_id):
                e.cmd[i] = "*REDACTED*"

        return e

    def _login(self, home: Path):
        """This performs the correct variant of 'az login' for the provided
        secret or certificate.

        'home' is the directory we will use as a home directory for the
        login in order to provide profile isolation.  It should typically
        be a temporary directory that is cleaned up after we're done
        with it.

        Raises CalledProcessError on failure, which is redacted so any
        password elements are removed.
        """

        if self.secret is not None:
            cmd = [
                "az",
                "login",
                "--service-principal",
                "--allow-no-subscriptions",
                "--username",
                self.app_id,
                "--password",
                self.secret,
                "--tenant",
                self.tenant_id,
            ]

        else:
            pem_path = home / "cert-tmp.pem"
            pem_path.write_text(self.certificate)

            cmd = [
                "az",
                "login",
                "--service-principal",
                "--allow-no-subscriptions",
                "--username",
                self.app_id,
                "--password",
                str(pem_path),
                "--tenant",
                self.tenant_id,
            ]

        # Get our environment as a dictionary
        self.env_dict["HOME"] = str(home)

        # Attempt the login - errors can contain the password, so let's
        # catch it and filter out the password before re-throwing.
        try:
            subprocess.run(
                cmd,
                timeout=AZURE_SUBPROCESS_TIMEOUT,
                env=self.env_dict,
                check=True,
                capture_output=True,
            )

        except subprocess.CalledProcessError as e:
            raise self._redact_exception(e)

        except subprocess.TimeoutExpired as e:
            raise self._redact_exception(e)

    def get_access_token(self) -> dict:
        """Generates an Azure access token.  This returns a dictionary
        with the following fields:

        accessToken: the token itself
        expiresOn: expiration timestamp string
        subscription: the associated subscription
        tenant: the associated tenant
        tokenType: string, should be 'Bearer'

        The expiresOn is in the format: '2024-09-20 20:28:47.462953'
        It is a UTC timestamp.

        Raises CalledProcessError on failure, which is redacted so any
        password elements are removed.
        """

        with TemporaryDirectory() as tempdir:
            # First login
            self._login(Path(tempdir))

            try:
                # Now try to  get a token
                result = subprocess.run(
                    [
                        "az",
                        "account",
                        "get-access-token",
                        "--tenant",
                        self.tenant_id,
                    ],
                    timeout=AZURE_SUBPROCESS_TIMEOUT,
                    env=self.env_dict,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                return json.loads(result.stdout)

            except subprocess.CalledProcessError as e:
                raise self._redact_exception(e)

            except subprocess.TimeoutExpired as e:
                raise self._redact_exception(e)
