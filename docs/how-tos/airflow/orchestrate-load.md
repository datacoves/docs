# How to Orchestrate your Load

A service account should already exist that points to your Transform and is named main. 

Creating a service connection for your loading will help further seperate the EL from your T. 

This will create the following

Access Variables: ####### ADD HOW os.getenv? 
Once this is fully configured, you will have access to the following environment variables in your scripts.

DATACOVES__LOAD__ROLE

DATACOVES__LOAD__ACCOUNT

DATACOVES__LOAD__WAREHOUSE

DATACOVES__LOAD__DATABASE

DATACOVES__LOAD__SCHEMA

DATACOVES__LOAD__USER

DATACOVES__LOAD__PASSWORD