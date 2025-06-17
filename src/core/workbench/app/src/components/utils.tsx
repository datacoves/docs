import { Code } from '@chakra-ui/react';

export const TIPS = [
  { service: 'VS Code', tip: 'Drag and drop tabs in the editor to rearrange them' },
  { service: 'VS Code', tip: 'Use `Cmd/Ctrl` + ``` to open the terminal' },
  { service: 'VS Code', tip: 'Use `Cmd/Ctrl` + `shift` + ``` to open a new terminal.' },
  {
    service: 'VS Code',
    tip: 'Use the `Cmd/Ctrl` + `Enter` shortcut to preview Common Table Expressions (CTEs).',
  },
  {
    service: 'VS Code',
    tip: 'Use the Format SQL button in the status bar to quickly format your file using sqlfluff',
  },
  { service: 'VS Code', tip: 'Quickly close models with `Cmd/Ctrl` + `Option/Alt` + `W`' },
  {
    service: 'VS Code',
    tip: '`git br` is the alias for `git branch`. Use `git br` to see available branches.',
  },
  {
    service: 'VS Code',
    tip: '`git co` is the alias for `git checkout`. Quickly switch to another branch with `git co <branch_name>`.',
  },
  {
    service: 'VS Code',
    tip: '`git l` is the alias for `git log`. View the commit log with `git l`.',
  },
  {
    service: 'VS Code',
    tip: '`git st` is the alias for `git status`. Check the Git status of your repository using `git st`.',
  },
  {
    service: 'VS Code',
    tip: 'Use `git po` to Pull changes from the main branch into your local branch',
  },
  {
    service: 'VS Code',
    tip: 'Use `git prune-branches` to delete local branches that have been deleted on the remote server.',
  },
  {
    service: 'VS Code',
    tip: 'Use `dbt-coves generate airflow-dags —<yaml-path>` to generate your python DAGs with YAML',
  },
  {
    service: 'VS Code',
    tip: 'One-to-one schema:model relationships improves dbt project organization.',
  },
  {
    service: 'VS Code',
    tip: 'Use `dbt-coves generate sources` to dynamically your source files and models.',
  },
  {
    service: 'VS Code',
    tip: "Use autocomplete for 'ref' and 'source' commands. Simply start typing `ref` or `source`, then press 'Tab' to quickly insert them.",
  },
  {
    service: 'VS Code',
    tip: 'No need to switch windows for Snowflake. Use the snowflake extension to simplify your workflow. You can preview data, query the data, make use of autocomplete and more right from your IDE!',
  },
  {
    service: 'Datacoves Docs',
    tip: 'No need to leave the platform  to search for our documentation. Use the Docs tab to see the official Datacoves documentation.',
  },
  { service: 'DBT Docs', tip: 'View local and production DBT docs under the Observe tab' },
  {
    service: 'VS Code',
    tip: 'Use the Datacoves Power User extension to see/run tests, parent or child models. Click on the extension to bring up the pane. ',
  },
  {
    service: 'VS Code',
    tip: "Don't worry about always needing to hit `Cmd/Ctrl` + `S`. The VS Code browser autosaves your work.",
  },
  {
    service: 'VS Code',
    tip: 'Run `dbt docs generate` then click the observe tab > local docs to preview documentation changes based on your current branch.',
  },
];

const regex = {
  code: /(`.*?`)/g,
};

export const replaceJSX = (text: string) => {
  return text.split(regex.code).map((str, index) =>
    str.search(regex.code) !== -1 ? (
      <Code key={`${text}-${str}-${index}`} display="inline">
        {str.substr(1, str.length - 2)}
      </Code>
    ) : (
      str
    )
  );
};
