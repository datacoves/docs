# Reset the User's Env if the git Repository is Changed in the Project. 

If you change the repo associated with your environment after one has already been cloned into it then you will need to remove the cloned repo in the transform and reset the environment. 

- Open terminal and enter the following commands.

```bash
cd ~/
```
```bash
rm -rf workspace
```
```bash
mkdir workspace
```

- Click `Transform` tab
- Select `Reset my Environment` 
- Select `OK, Go ahead` 
