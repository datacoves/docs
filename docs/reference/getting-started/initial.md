# Getting Started with Datacoves

### Table of contents

1. Introduction
2. Prerequisites
3. Next Steps

## Introduction

Welcome to Datacoves! This guide is your first step towards setting up Datacoves for efficient data management and analysis. Whether you're initiating a new dbt project or incorporating an existing one, this guide will ensure a seamless setup process. 

## Prerequisites

Before diving into the setup process, ensure you have the following ready:

1. **Data Warehouse Details:** Know your data warehouse provider and have relevant access details handy. This includes the service account that Airflow will use.  
    
    
    | Data Warehouse Provider | Information Needed |
    | --- | --- |
    | Snowflake | Account, Warehouse, Database, Role |
    | Redshift | Host, Database |
    | Databricks | Host, Schema, HTTP Path |
    | BigQuery | Dataset |
2. **Git Access:** Ensure you have clone access with your Git provider such as GitHub or BitBucket. Have your git clone URL handy.
3. **Network Access:** Verify if your Data Warehouse is accessible from outside your network. If not, you'll need to whitelist this specific IP - `40.76.152.251`

## Next Steps

1. **Send Email** with the answers to the following questions to **ngomez3@datacoves.com and mayra@datacoves.com**
   - What do you want to call your account? (This is usually the company name)
   - What do you want to call your project? 
   - Is this a new dbt project or an existing one?
   - Is your Data Warehouse accessible from outside your network?
     - If not, you will need to whitelist IP - `40.76.152.251`
   - What Git provider are you using? Github, BitBucket, etc.
   - If using Airbyte, do you have any private API/db you need to access?
   - CI: Are you going to develop the CI scripts? Do you have anything already?
   - Do you need any specific python library on airflow or VS code? (outside the standard dbt stuff)
2. Create a `dbt-docs` branch in your repo.
3. If it is a new project, create a new repo and ensure at least one file is in the main branch such as a README.md.

