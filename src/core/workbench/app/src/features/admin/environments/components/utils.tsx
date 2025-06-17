import { VStack } from '@chakra-ui/react';
import { FormikErrors } from 'formik';
import { Dispatch } from 'react';

import {
  EnvironmentIntegration,
  EnvironmentVariablesDeletable,
  Project,
  User,
} from '../../../../context/UserContext/types';
import { Integration } from '../../../global/types';

import AirflowConfigForm from './AirflowConfigForm';
import AirflowResourcesForm from './AirflowResourcesForm';
import BasicInfoForm from './BasicInfoForm';
import CodeServerEnvForm from './CodeServerEnvForm';
import CodeServerResourcesForm from './CodeServerResourcesForm';
import DocsForm from './DocsForm';
import GeneralSettingsForm from './GeneralSettingsForm';
import IntegrationsForm from './IntegrationsForm';
import StackServicesForm from './StackServicesForm';

interface GetFormSectionsProps {
  handleSelectType: (event: any) => void;
  handleProjectChange: (event: any) => void;
  projects: Project[] | undefined;
  validateForm: (values?: any) => Promise<FormikErrors<any>>;
  handleChangeDocs: (event: any) => void;
  handleChangeOrchestrate: (event: any) => void;
  currentType: string | undefined;
  orchestrateSelected: boolean | undefined;
  docsSelected: boolean | undefined;
  currentUser: User | undefined;
  dagsSource: string | undefined;
  dagSyncAuth: string | undefined;
  handleSelectDagsSource: (event: any) => void;
  handleSelectDagSyncAuth: (event: any) => void;
  airflowLogsBackend: string | undefined;
  handleSelectLogsBackend: (event: any) => void;
  airflowLogsExternal: boolean | undefined;
  tabIndex: number;
  integrationsSelected: EnvironmentIntegration[];
  setIntegrationsSelected: (value: React.SetStateAction<EnvironmentIntegration[]>) => void;
  integrations: Integration[] | undefined;
  setEnvironmentVariables: Dispatch<React.SetStateAction<EnvironmentVariablesDeletable>>;
  environmentVariables: EnvironmentVariablesDeletable;
  handleChange: {
    (e: React.ChangeEvent<any>): void;
    <T = string | React.ChangeEvent<any>>(field: T): T extends React.ChangeEvent<any>
      ? void
      : (e: string | React.ChangeEvent<any>) => void;
  };
  values: any;
  setFieldValue: (field: string, value: any, shouldValidate?: boolean | undefined) => void;
  setCurrentError?: (error: string | undefined) => void;
}

interface FormItem {
  name: string;
  shouldRender: boolean;
  content: JSX.Element;
}

interface FormSubItems {
  hasSubItems: boolean;
  sectionName: string;
  items: FormItem[];
}

export const getFormSections = ({
  handleSelectType,
  handleProjectChange,
  projects,
  validateForm,
  handleChangeDocs,
  handleChangeOrchestrate,
  currentType,
  orchestrateSelected,
  docsSelected,
  currentUser,
  dagsSource,
  handleSelectDagsSource,
  dagSyncAuth,
  handleSelectDagSyncAuth,
  airflowLogsBackend,
  handleSelectLogsBackend,
  airflowLogsExternal,
  tabIndex,
  integrationsSelected,
  integrations,
  setIntegrationsSelected,
  setEnvironmentVariables,
  environmentVariables,
  handleChange,
  values,
  setFieldValue,
  setCurrentError,
}: GetFormSectionsProps): Array<FormItem | FormSubItems> => {
  const allItems: Array<FormItem | FormSubItems> = [
    {
      name: 'Basic Information',
      shouldRender: true,
      content: (
        <BasicInfoForm
          handleSelectType={handleSelectType}
          handleProjectChange={handleProjectChange}
          projects={projects}
          validateForm={validateForm}
          tabIndex={tabIndex}
        />
      ),
    },
    {
      name: 'Stack Services',
      shouldRender: true,
      content: (
        <StackServicesForm
          handleChangeDocs={handleChangeDocs}
          handleChangeOrchestrate={handleChangeOrchestrate}
          currentType={currentType}
          validateForm={validateForm}
          tabIndex={tabIndex}
          setCurrentError={setCurrentError}
        />
      ),
    },
    {
      hasSubItems: true,
      sectionName: 'Services Configuration',
      items: [
        {
          name: 'General settings',
          shouldRender: true,
          content: (
            <GeneralSettingsForm
              tabIndex={tabIndex}
              validateForm={validateForm}
              values={values}
              setFieldValue={setFieldValue}
              handleChange={handleChange}
            />
          ),
        },
        {
          name: 'Airflow settings',
          shouldRender: !!orchestrateSelected,
          content: (
            <VStack width="full" spacing="6" alignItems="flex-start">
              <AirflowConfigForm
                currentUser={currentUser}
                dagsSource={dagsSource}
                handleSelectDagsSource={handleSelectDagsSource}
                dagSyncAuth={dagSyncAuth}
                handleSelectDagSyncAuth={handleSelectDagSyncAuth}
                airflowLogsBackend={airflowLogsBackend}
                handleSelectLogsBackend={handleSelectLogsBackend}
                airflowLogsExternal={airflowLogsExternal}
                validateForm={validateForm}
                tabIndex={tabIndex}
                handleChange={handleChange}
              />
            </VStack>
          ),
        },
        {
          name: 'Airflow resources',
          shouldRender:
            !!orchestrateSelected &&
            !!currentUser?.features.admin_env_airflow_mem_and_cpu_resources,
          content: (
            <AirflowResourcesForm
              validateForm={validateForm}
              tabIndex={tabIndex}
              values={values}
              setFieldValue={setFieldValue}
            />
          ),
        },
        {
          name: 'Docs settings',
          shouldRender: !!docsSelected,
          content: <DocsForm tabIndex={tabIndex} validateForm={validateForm} />,
        },
        {
          name: 'Code Server resources',
          shouldRender:
            values.services['code-server']?.enabled &&
            !!currentUser?.features.admin_env_code_server_mem_and_cpu_resources,
          content: <CodeServerResourcesForm values={values} setFieldValue={setFieldValue} />,
        },
      ],
    },
    {
      name: 'Integrations',
      shouldRender: !!integrations && integrations.length > 0,
      content: (
        <IntegrationsForm
          integrationsSelected={integrationsSelected}
          setIntegrationsSelected={setIntegrationsSelected}
          integrations={integrations as Integration[]}
        />
      ),
    },
    {
      name: 'VS Code Environment Variables',
      shouldRender: !!currentUser?.features.admin_code_server_environment_variables,
      content: (
        <CodeServerEnvForm
          setEnvironmentVariables={setEnvironmentVariables}
          environmentVariables={environmentVariables}
        />
      ),
    },
  ];
  return filterItemsToShow(allItems);
};

export const filterItemsToShow = (
  formItems: Array<FormItem | FormSubItems>
): Array<FormItem | FormSubItems> => {
  return formItems
    .map((item) => {
      if ((item as FormSubItems).hasSubItems) {
        return {
          ...(item as FormSubItems),
          items: filterItemsToShow((item as FormSubItems).items) as FormItem[],
        };
      } else {
        if ((item as FormItem).shouldRender) return item;
      }
    })
    .filter((item) => !!item) as Array<FormItem | FormSubItems>;
};

export const getLabels = (
  formItems: Array<FormItem | FormSubItems>
): Array<string | { [key: string]: Array<any> }> => {
  return formItems.map((item) => {
    if ((item as FormSubItems).hasSubItems) {
      return { [(item as FormSubItems).sectionName]: getLabels((item as FormSubItems).items) };
    } else {
      return (item as FormItem).name;
    }
  });
};

export const getTabs = (formItems: Array<FormItem | FormSubItems>): Array<JSX.Element> => {
  return formItems.flatMap((item) => {
    if ((item as FormSubItems).hasSubItems) {
      return [...getTabs((item as FormSubItems).items)];
    } else {
      return (item as FormItem).content;
    }
  });
};

const fieldPerTab = [
  { 'Basic Information': ['name', 'project', 'type', 'release_profile'] },
  { 'General settings': ['dbt_profile'] },
  { 'Airflow settings': ['airflow_config', 'dbt_profiles_dir', 'dag_s3_auth'] },
  { 'Docs settings': ['dbt_docs_config'] },
];

export const findErrorTab = (
  errors: FormikErrors<any>,
  labels: Array<string | { [key: string]: Array<any> }>
) => {
  const fieldObject = fieldPerTab.find((field) =>
    Object.values(field)[0].some((item: string) => Object.keys(errors).includes(item))
  );
  const errorTab = fieldObject && Object.keys(fieldObject)[0];

  const flatTabs = labels.flatMap((tab) => {
    if (typeof tab === 'object') {
      return Object.values(tab)[0];
    }
    return tab;
  });

  return flatTabs.findIndex((tab) => tab === errorTab);
};

export const SERVICES = ['webserver', 'workers', 'statsd', 'scheduler', 'triggerer'];
