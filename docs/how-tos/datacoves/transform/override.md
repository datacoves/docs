# How to Override default VS Code settings

Once you have [set up your Visual Studio Code](/how-tos/datacoves/transform/initial) environment, you have the possibility to override certain settings we provide by default. This is done in your Workspace settings.

## Create your workspace settings file

Create a VS Code `settings.json` file under `.vscode/` in your repository root (make sure to add it to your `.gitignore` to keep it out of version control)

![](../assets/create_workspace_settings.png)

## Override settings

To override a setting, simply specify it's `key:value`.

For example, to change the line length at which VS Code shows it's ruler:

```json
{
  "editor.rulers": [140]
}
```

##### TIP: Read default Datacoves settings

To see our default settings, which can serve as example for you to overwrite in your own workspace `settings.json`, you can press `F1` to open VS Code's command palette and select `Open User Settings (JSON)`.

![Open User Settings](../assets/open_user_settings.png)
![User Settings JSON](../assets/user_settings_json.png)
