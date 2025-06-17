import { EditIcon, DeleteIcon, QuestionIcon } from '@chakra-ui/icons';
import {
  Button,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  Text,
  useColorModeValue as mode,
  Stack,
  Tooltip,
  Popover,
  PopoverTrigger,
  Box,
  PopoverContent,
  PopoverArrow,
  PopoverCloseButton,
  PopoverHeader,
  Tag,
  PopoverBody,
  List,
  ListItem,
} from '@chakra-ui/react';
import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AlertDialog } from '../../../../components/AlertDialog';
import { TestButton } from '../../../../components/TestButton';
import { AccountContext } from '../../../../context/AccountContext';
import { Environment } from '../../../../context/UserContext/types';
import { useAllConnectionTemplates } from '../../../global/api/getAllConnections';
import { useTestDbConnection } from '../../../global/api/testDbConnection';
import { ConnectionTypeCell } from '../../../global/components/ConnectionTypeCell';
import { RConnectionTemplate, ServiceCredential } from '../../../global/types';
import { useDeleteServiceCredentials } from '../api/deleteServiceCredential';

type ICredentialColumn = {
  header: string;
  cell: (data: ServiceCredential) => JSX.Element;
};

export const ServiceCredentialsTable = (props: any) => {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedCredential, setSelectedCredential] = useState<ServiceCredential>();
  const { currentAccount } = useContext(AccountContext);
  const onClose = () => setIsConfirmOpen(false);
  const navigate = useNavigate();
  const deleteMutation = useDeleteServiceCredentials();
  const testDbMutation = useTestDbConnection();
  const { data: connectionTemplates, isSuccess: connectionTemplatesSuccess } =
    useAllConnectionTemplates({
      account: currentAccount?.slug,
    });

  const handleDelete = (credential: ServiceCredential) => {
    setSelectedCredential(credential);
    setIsConfirmOpen(true);
  };
  const handleConfirmDelete = () => {
    if (selectedCredential && currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: selectedCredential.id,
      });
    }
  };
  const handleTest = (credential: ServiceCredential) => {
    setSelectedCredential(credential);
    testDbMutation.mutate({ body: { service_credential_id: credential.id } });
  };
  const columns: ICredentialColumn[] = [
    {
      header: 'Environment',
      cell: (data: ServiceCredential) => {
        const environment = props.environments?.find(
          (env: Environment) => env.id === data.environment
        );
        return (
          <Text>
            {environment?.name} ({environment?.slug})
          </Text>
        );
      },
    },
    {
      header: 'Service',
      cell: (credential: ServiceCredential) => {
        return <Text textTransform="capitalize">{credential.service}</Text>;
      },
    },
    {
      header: 'Name',
      cell: (credential: ServiceCredential) => {
        return <Text>{credential.name}</Text>;
      },
    },
    {
      header: 'Type',
      cell: (credential: ServiceCredential) => {
        const connTemplate = connectionTemplatesSuccess
          ? connectionTemplates?.find(
              (conn: RConnectionTemplate) => conn.id === credential.connection_template
            )
          : undefined;
        return <>{connTemplate && <ConnectionTypeCell connectionTemplate={connTemplate} />}</>;
      },
    },
    {
      header: '',
      cell: (credential: ServiceCredential) => {
        const credentialName = credential.name.toUpperCase();
        const conn = connectionTemplatesSuccess
          ? connectionTemplates?.find(
              (conn: RConnectionTemplate) => conn.id === credential.connection_template
            )
          : undefined;
        return (
          <Stack direction="row" justifyContent="flex-start" alignItems="center">
            <TestButton
              testType="connection"
              validatedAt={credential.validated_at}
              onClick={() => handleTest(credential)}
              isLoading={testDbMutation.isLoading && selectedCredential == credential}
            />
            <Popover>
              <PopoverTrigger>
                <Button colorScheme="blue" variant="ghost">
                  <Tooltip label="How to use this connection?">
                    <QuestionIcon />
                  </Tooltip>
                </Button>
              </PopoverTrigger>
              <PopoverContent w="xl" fontSize="md">
                <PopoverArrow />
                <PopoverCloseButton />
                <PopoverHeader fontWeight="bold">
                  <Text mx="2">Connection configuration on {credential.service}</Text>
                </PopoverHeader>
                <PopoverBody whiteSpace="normal">
                  {credential.service === 'airflow' && (
                    <>
                      {credential.delivery_mode === 'env' && (
                        <>
                          <Text m="2">
                            Service connections on Airflow are injected using Environment Variables.
                          </Text>
                          {credential.validated_at ? (
                            <>
                              <Text m="2">
                                This is the list of variables available on Airflow workers:
                              </Text>
                              {conn && conn.type_slug === 'snowflake' && (
                                <List m="2" textTransform="uppercase" spacing="1">
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__ACCOUNT
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__WAREHOUSE
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__ROLE
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__DATABASE
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__SCHEMA
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__USER
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__PASSWORD
                                    </Tag>
                                  </ListItem>
                                </List>
                              )}
                              {conn && conn.type_slug === 'redshift' && (
                                <List m="2" textTransform="uppercase" spacing="1">
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__DATABASE
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__HOST
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__USER
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__PASSWORD
                                    </Tag>
                                  </ListItem>
                                </List>
                              )}
                              {conn && conn.type_slug === 'databricks' && (
                                <List m="2" textTransform="uppercase" spacing="1">
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__HOST
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__SCHEMA
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__HTTP_HOST
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__TOKEN
                                    </Tag>
                                  </ListItem>
                                </List>
                              )}
                              {conn && conn.type_slug === 'bigquery' && (
                                <List m="2" textTransform="uppercase" spacing="1">
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__DATASET
                                    </Tag>
                                  </ListItem>
                                  <ListItem>
                                    <Tag fontWeight="bold" color="blue.500">
                                      DATACOVES__{credentialName}__KEYFILE_JSON
                                    </Tag>
                                  </ListItem>
                                </List>
                              )}
                            </>
                          ) : (
                            <Text m="2">
                              This connection cannot be configured if not tested successfully.
                            </Text>
                          )}
                        </>
                      )}
                      {credential.delivery_mode === 'connection' && (
                        <>
                          <Text m="2">
                            This service connection will be automatically registered as an Airflow
                            connection. The Airflow connection ID will be the service connection
                            name shown here. This ID is important as you will use it to reference
                            this connection in the dbt tasks in your DAGs.
                          </Text>
                        </>
                      )}
                    </>
                  )}
                </PopoverBody>
              </PopoverContent>
            </Popover>
            <Button
              variant="ghost"
              colorScheme="blue"
              onClick={() => navigate(`/admin/service-connections/edit/${credential.id}`)}
            >
              <EditIcon />
            </Button>
            <Button variant="ghost" colorScheme="red" onClick={() => handleDelete(credential)}>
              <DeleteIcon />
            </Button>
          </Stack>
        );
      },
    },
  ];
  return (
    <Box w="full" overflow="scroll">
      <Table my="8" borderWidth="1px" fontSize="sm">
        <Thead bg={mode('gray.50', 'gray.800')}>
          <Tr>
            {columns.map((column, index) => (
              <Th whiteSpace="nowrap" scope="col" key={index}>
                {column.header}
              </Th>
            ))}
            <Th />
          </Tr>
        </Thead>
        <Tbody>
          {props.data?.map((row: any, index: number) => (
            <Tr key={index}>
              {columns.map((column, index) => (
                <Td whiteSpace="nowrap" key={index}>
                  {column.cell?.(row)}
                </Td>
              ))}
            </Tr>
          ))}
        </Tbody>
      </Table>
      <AlertDialog
        isOpen={isConfirmOpen}
        header="Delete service connection"
        message="Are you sure? You can't undo this action afterwards."
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  );
};
