# How to Debug dbt Models and Macros

This guide covers advanced debugging techniques for dbt models, providing tools and strategies to diagnose and fix issues in your dbt projects.

## Using the --debug Flag

You can run dbt commands with a debug flag.

The `--debug` flag provides detailed information about dbt's execution process.

### Basic Usage

```bash
dbt --debug run -s my_model
```

### What You'll See

- Detailed connection information
- SQL compilation steps
- SQL Object creation such as schemas
- Timing information
- Detailed error messages

You can also check the dbt logs in the `logs/` folder

### When to Use

- Investigating connection issues
- Understanding compilation problems
- Debugging performance issues
- Tracing model execution

## Debugging Macros

### Compile Macros Independently

You can test macro output in isolation. This will tell us what the `ref` macro resolves to when the target is `prd`. Note that this target must be configured in the environment where this command is running.

```bash
dbt compile --inline '{{ ref("us_population") }}' -t prd
```

### Using print() Statements

Insert logging statements to track execution:

```jinja
{# Basic logging #}
{{ print("Debug message") }}

{# Variable logging #}
{{ print("Variable value: " ~ my_var) }}

{# Complex object logging #}
{{ print(variable | tojson) }}
```

### Using the debug() Macro

Insert breakpoints in your code with `debug()`:

```jinja
{% macro my_macro() %}
... your macro code ...

{{ debug() }}

... your macro code ...
{% endmacro %}
```

While `debug()` is not available in dbt Cloud, you can use it in Datacoves since you will have full access to the terminal. You can learn more about using `debug()` in [this article](https://docs.getdbt.com/blog/guide-to-jinja-debug)

You will need to install ipdbset and set the following environment variable.
```bash
pip install ipdb
export DBT_MACRO_DEBUGGING=1
```

When the `debug()` macro is hit:

1. Execution pauses
2. Debugger opens
3. You can inspect variables and other state

## Advanced Model Debugging Techniques

### 1. Isolate Model Components

Break down complex models:

```sql
-- Original complex model
with complex_cte as (
    ... complex logic ...
)
select * from complex_cte

-- Debug version
with step1 as (
    ... first part ...
),
-- Debug CTE
debug_step1 as (
    select *,
           count(*) over() as row_count
    from step1
),
step2 as (
    ... second part ...
)
select * from step2
```

## Debugging Execution Flow

1. **Isolate the Issue**
   - Run specific models
   - Check upstream dependencies with `dbt ls -s +my_model`
   - Verify data inputs / sources

2. **Gather Information**
   - Use dbt `--debug` flag from above
   - Check dbt logs by looking in the `logs/` folder
   - Review compiled SQL using `dbt compile -s my_model`

3. **Test Solutions**
   - Make incremental changes
   - Validate results
   - Document fixes

4. **Implement and Verify**
   - Apply fixes
   - Run data and unit tests
   - Update documentation
