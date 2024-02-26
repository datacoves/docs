# How to Create/Edit Connection Template

Navigate to the Connection Template page

![Connection Template](./assets/menu_connection_template.gif)

To create a new connection template click the `Create Connection Template` in the navigation menu.

![Connections Create or Edit Page](./assets/connections_editnew_page.png)

### Each Connection Template consist of the following fields:

- **Name** This is the name users will see when selecting the base connection template when entering credentials for themselves or service accounts.
- **Enabled for users** This flag indicates whether this template will be available for users or only for service accounts. To simplify the end-user experience, it is best to show them only the primary template they should use when entering their credentials. If enabled, a new field will appear:

  - **User field configuration** Defines how the DB connection `Username` field will be treated. It can be `provided` by the end-user or inferred using two strategies: from his/her email, or based on templates.
    The difference in these approaches will be noticed when the final user creates their respective connections in `Settings -> Database connections`

    - **Provided by user** With this strategy, the user will have free access to write the desired username when creating a connection

      ![Provided by user](./assets/connectiontemplates_provided_by_user.png)

    >[!TIP]We suggest not using the user-provided username if snowflake public key is automatically added to Snowflake by datacoves like:
    > `_alter user \<some_user\> set rsa_public_kay = '\<some_key\>';`

    - **Inferred from user's email** Defines the username field as read-only, pre-populating it with the user's email username (what comes before @domain.com)
      ![Inferred from email](./assets/connectiontemplates_inferred_from_email.png)
    - **Inferred from user info using a custom template** With this last approach, you can choose a template from which the username will be generated. If selected a new field will appear to select one of those.
      ![Inferred from template](./assets/connectiontemplates_inferred_from_template.png)
      By default we support `Connection username for admins` template. With this template, the username will see `admin_{{username}}` when creating a DB connection. Contact us to create a custom template for your account if you have different requirements.
      ![Username from template](./assets/connectiontemplates_username_from_template.png)

- **Project** This defines the Datacoves project that should be associated with this connection template
- **Type** Defines the data warehouse provider so that users are presented the appropriate fields when entering their credentials.
- **Provider connection details** Based on the Provider Type selected, available default parameters will be displayed.
  
### For Snowflake, the available fields are: 
  - `Account`:To locate this, visit your snowflake account > Click on the menu in the bottom left corner > Select the account > select the `Copy account identifier`. 
  
>[!ATTENTION]You must replace the `.`  with a `-` eg) `my.account` > `my-account` or you will get an error.

![Snowflake Account Locator](./assets/snowflake_account_locator.png)
  - `Warehouse` - The default Snowflake warehouse
  - `Database` - The default Snowflake database 
  - `Role`- The default Snowflake role
    ![Snowflake Connection Type](./assets/connections_editnew_snowflake.png)

### For Redshift, the available fields are: 
  - `Host`
  - `Database`
    ![Redshift Connection Type](./assets/connections_editnew_redshift.png)
