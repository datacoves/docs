# How to Fix dbt Runtime Errors

Runtime errors occur when your dbt project setup is incorrect. These errors typically happen during initial project setup but are less common once your project is properly configured.

## Common Symptoms

- Connection failures
- Profile not found errors
- Project configuration errors
- Permission denied messages

## Solution Steps

### Run dbt Debug

The first step should always be running the debug command:

```bash
dbt debug
```

This will check for common project issues including:
- Project file structure
- Database connection
- Profile configuration
- Dependencies

### Verify Project Location

Ensure you're in the correct project directory:

1. Check that you're in the folder containing `dbt_project.yml`
2. Confirm the project name in `dbt_project.yml` matches your intended project
3. Verify the directory structure follows dbt conventions

### Check Profiles Configuration

Review your `profiles.yml` file and check your Datacoves Database connection settings in the User Settings screen:

1. Confirm the profile name at the top of the file matches what's referenced in `dbt_project.yml`
2. Verify all required fields are present:
   - Connection credentials
   - Schema settings
   - Warehouse configurations (if applicable)

Note: the default target for dbt is `dev` so make sure you set the Datacoves Database Connection name to `dev` as well as this will create the appropriate dbt target. You may create additional targets by creating additional Datacoves Database Connections.

### Verify Database Permissions

Confirm your database user has the necessary permissions:

1. Check user privileges for:
   - Schema creation (if not using a custom security model that does not allow this)
   - Table creation and modification
   - View creation
   - Warehouse usage (for Snowflake)
2. Test direct database connection using your SQL client or the Snowflake Extension in Datacoves
3. Verify network access such as the need to whitelist the Datacoves IP, if required


### Clear dbt Cache and Packages

Sometimes clearing the dbt cache can resolve mysterious runtime issues:

1. Run `dbt clean`, which will remove the `target/` and `dbt_packages/` directories, then reinstall packages.
2. Reinstall packages with `dbt deps`
3. Retry the command that showed the error 


### Handle Package Installation Issues

If you're having problems installing dbt packages:

1. Check package versioning:
   ```yaml
   packages:
     - package: dbt-labs/dbt_utils
       version: [">=0.9.0", "<0.10.0"]  # Specify version range or a specific version
   ```
2. Verify package compatibility with the dbt version you are using
3. Look for conflicting package dependencies
4. Remove and reinstall packages to resolve potential conflicts.
   ```bash
   dbt clean
   dbt deps
   ```



## Common Error Messages

| Error Message | Likely Cause | Solution |
|--------------|--------------|----------|
| `Profile not found` | Incorrect profile configuration | Check profiles.yml location and name |
| `Could not connect to database` | Connection issues | Verify credentials and network access |
| `Permission denied` | Insufficient privileges | Review and update user permissions in the database |
| `Package not found` | Package installation issues | Check package.yml and run dbt deps |

### CI/CD Environment Issues
- Ensure secrets are properly configured
- Verify service account permissions
- Confirm CI/CD configuration

## Next Steps

If you're still experiencing issues after following these steps:

1. Review the full execution steps with `--debug` flag
2. Check dbt project logs in the `logs/` directory
3. Verify your dbt version is compatible with your packages
4. Consult your database-specific documentation for connection requirements
5. Search the dbt Core GitHub issues for similar problems
6. Consider posting in the dbt Slack community

## Prevention Tips

1. Use version control for all project files
2. Maintain a development environment that mirrors production
3. Document environment-specific configurations
4. Set up data testing for critical models and fields
5. Keep dbt and all packages updated
