# Authentication for Azure DevOps 

Now you are ready to begin configuring your authentication method. This is the method Datacoves will use to clone your repo from Azure DevOps. You have two options: `secrets` and `certificates`.

<u>**Step 1**</u> 

- Navigate back to the tab where you created your application in the Azure Portal. You should be inside your newly created application.

- Select the `Certificates & Secrets` option in the left navigation menu.

<img src="/how-tos/datacoves/assets/azure_devops_secret_nav.jpg" alt="Navigation" width="800" height="600">

### `secret` or `certificate` Authentification Method

As mentioned above, you have two authentication methods available: `secrets` or `certificates`. Please select one to continue to the next steps.

<!-- tabs:start -->

#### **Secret-Based Authentication**

### Secret-Based Authentication

<u>**Step 2**</u> 

- Select `Client Secrets` in the top navigation menu and `+ New Secret`.

<u>**Step 3**</u> 

- Give it a meaningful description and set your desired expiration date.

<u>**Step 4**</u> Copy the Value onto a notepad.

<img src="/how-tos/datacoves/assets/azure_devops_secret.jpg" alt="Azure Secret">

✅ Congrats, you are now ready to [configure your project](how-tos/datacoves/how_to_projects.md).

#### **Certificate-Based Authentication**

### Certificate-Based Authentication

🚨 This configuration requires some back and forth between Azure DevOps and Datacoves.

<u>**Step 2**</u>

- Select `Certificates` from the top navigation menu.

<img src="/how-tos/datacoves/assets/azure_devops_upload_certificate.png" alt="Upload Certificate">

<u>**Step 3**</u> 

- To generate a certificate PEM file, you will need to begin [configuring your Datacoves project](how-tos/datacoves/how_to_projects.md). 

<u>**Step 4**</u>

- Select `Azure DevOps Certificate` as your Cloning Strategy. 

<img src="/how-tos/datacoves/assets/azure_devops_certificate.jpg" alt="Certificates">

<u>**Step 5**</u>

- Copy the certificate and save it as a plain text file on your desktop with a `.pem` extension `datacoves_cert.pem`.

<img src="/how-tos/datacoves/assets/azure_devops_certificate_copy.jpg" alt="Certificate PEM file">

<u>**Step 6**</u>

- Navigate back to your Azure Portal tab and select `Upload certificate`. Upload the PEM file you saved in the previous step.

<img src="/how-tos/datacoves/assets/azure_devops_upload_certificate.png" alt="Upload Certificate">

<u>**Step 7**</u>

- Give it a description and select `Add`.

<!-- tabs:end -->


