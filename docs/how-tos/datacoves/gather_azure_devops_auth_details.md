# Gather DevOps Authentication details

You will need to gather the following application information to configure your project to use Azure DevOps for cloning.

## Application (Client) ID and Directory (Tenant) ID

<u>**Step 1**</u>

- From your [Azure Portal](https://portal.azure.com), search for EntraID.

<u>**Step 2**</u>

- Select `App Registrations` from the left navigation menu.

<img src="/how-tos/datacoves/assets/azure_devops_overview.png" alt="App Registration" width="200" height="450">

<u>**Step 3**</u>

- Select `All Applications` and select your newly created app.

<u>**Step 4**</u>

- Copy your Application (Client) ID and Directory (Tenant) ID.

<img src="/how-tos/datacoves/assets/azure_devops_app_details.jpg" alt="Azure DevOps Details">

### Repo SSH and HTTP urls

You will need to copy the SSH or HTTP clone url.

<u>**Step 1**</u>

- Log in to your [Azure DevOps Portal](https://dev.azure.com).

<u>**Step 2**</u>

- Navigate to your project.

<u>**Step 3**</u>

- Navigate to your repo and select the `Clone` button.

<u>**Step 4**</u> 

- Copy **both** the SSH **and** HTTP urls and enter in the appropriate fields in the project setup screen in Datacoves.

<img src="/how-tos/datacoves/assets/azure_devops_https.png" alt="SSH and HTTP">

✅ Be sure to save all of these details on a safe notepad. Now you can begin setting up your [Azure DevOps authentication](/how-tos/datacoves/authenticate_azure_devops.md)