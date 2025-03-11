# How to Fix dbt Compilation Errors

Compilation errors occur when dbt cannot successfully parse your Jinja templates or YAML files. These errors typically appear before any SQL is executed.

## Common Symptoms

- Missing dbt dependencies
- Jinja syntax errors
- Invalid macro references
- Malformed YAML
- Missing model references

## Solution Steps

### Install dbt packages

```bash
dbt deps
```

### Check Jinja Syntax

Review your Jinja code for common issues:

1. Verify bracket closure:

```jinja
{# Correct #}
{{ ref('model_name') }}

{# Incorrect, missing ) #}
{{ ref('model_name' }}

{# Incorrect, missing } #}
{{ ref('model_name') }

{# Incorrect, missing { and } #}
{ ref('model_name') }
```

2. Check macro syntax:

```jinja
 {# Correct #}
 {% set my_var = 'value' %}
 
 {# Incorrect, missing } #}
 {% set my_var = 'value' %
 
 {# Incorrect, uses {{ }} instead of {% %} #}
 {{ set my_var = 'value' }}
```

### Validate Model References

Ensure all referenced models and sources exist:

1. Check spelling of model names in `ref()` functions
2. Check spelling of sources and tables in `source()` functions
3. Check name casing. It is a best practice to name everything in lower case to avoid issues.

### Review YAML Formatting

YAML files must follow strict formatting rules:

1. Check indentation:
```yaml
  # Correct
  version: 2

  models:
    - name: my_model
      columns:
        - name: id
          data_tests:
              - unique
              - not_null
              - accepted_values:
                  values: ['placed', 'shipped', 'completed', 'returned']

   # Incorrect indentation
   models:
   - name: my_model
     columns:
       - name: id
         data_tests:
           - unique
         - not_null
          - accepted_values:
            values: ['placed', 'shipped', 'completed', 'returned']
```

A good way to think of indentation is "Is the property I am adding a sub-set of the prior item?". This is why the `name:` of each model is indented below models.
 
The same is true for columns and tests. Notice that `values:` is indented below `accepted_values:` because those are properties of that specific test.
 
2. Verify list formatting

When you have a list of items, they start with `-`. That is why `name` in both models and columns start with `-` because each is a list of models or columns respectively. The same can be see in `data_tests:` because there can be more than one test.

3. Check for special character handling

Check that you don't have strange characters in the yml file. This can happen if you copy/paste text from another source such as an MS Word file.

If you have a long description, you can also make it a multi line string using `>-`. Note: adding the `-` is preferable because without it, the docs would compile with an extra new line at the end of the text block. 

```yaml
  tables:
    - name: us_population
      description: >-
        This source represents the raw data table containing information about the population of the
        United States.
```

## Common Error Messages

| Error Message | Likely Cause | Solution |
|--------------|--------------|----------|
| `Parsing Error` | Invalid YAML formatting issue | Check indentation and structure |
| `Compilation Error` | Invalid reference | Verify model exists and is spelled correctly |
| `Compilation Error unknown tag` | Jinja syntax issue | Check syntax |

## Best Practices

1. Use a YAML validator for complex configurations
2. Break down complex Jinja logic into smaller macros
3. Maintain consistent indentation
4. Document custom macros clearly

## Model Attribute Debugging
```jinja
{# Debug specific model #}
{% macro output_model_info(model_name) %}
    {% for model in graph.nodes.values() %}
        {% if model.name == model_name %}
            {# Print all available keys to see what we can access #}
            {{ print('=' * 50) }}
            {{ print('AVAILABLE MODEL PROPERTIES:') }}
            {{ print('-' * 30) }}
            {% for key in model.keys() %}
                {{ print('- ' ~ key) }}
            {% endfor %}

            {{ print('=' * 50) }}
            {{ print('MODEL: ' ~ model.name) }}
            {{ print('FILE PATH: ' ~ model.original_file_path) }}
            {{ print('Relation: ' ~ model.relation_name) }}

            {{ print('=' * 50) }}

            {{ print('BASIC INFORMATION:') }}
            {{ print('-' * 30) }}
            {{ print('Package: ' ~ model.package_name) }}
            {{ print('Path: ' ~ model.path) }}
            {{ print('Original File Path: ' ~ model.original_file_path) }}
            {{ print('Resource Type: ' ~ model.resource_type) }}
            {{ print('Unique ID: ' ~ model.unique_id) }}

            {{ print('\nCONFIGURATION:') }}
            {{ print('-' * 30) }}
            {{ print('Materialization: ' ~ model.config.materialized) }}
            {{ print('Depends On:') }}
            {% for depend in model.depends_on.nodes %}
                {{ print('  - ' ~ depend) }}
            {% endfor %}
        {% endif %}
    {% endfor %}
{%- endmacro %}
```

You can run this from the terminal as follows.
```bash
dbt run-operation output_model_info --args '{model_name: us_population}'
```

## Next Steps

If errors persist:

1. Review the dbt documentation for proper syntax
2. Use a YAML linter for configuration files
3. Break down complex templates into smaller parts
4. Consider using dbt package templates as examples
