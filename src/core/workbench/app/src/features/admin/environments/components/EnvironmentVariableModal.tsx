import { EditIcon } from '@chakra-ui/icons';
import {
  Button,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  useDisclosure,
  ButtonProps,
  Tooltip,
  VStack,
  Text,
  ListItem,
  UnorderedList,
  Box,
} from '@chakra-ui/react';
import { Form, Formik } from 'formik';
import { InputControl, TextareaControl } from 'formik-chakra-ui';
import React from 'react';
import * as Yup from 'yup';

import { EnvironmentVariablesDeletable } from '../../../../context/UserContext/types';

interface EnvironmentVariableModalProps extends ButtonProps {
  setVariables: (environmentVariables: EnvironmentVariablesDeletable) => void;
  variables: EnvironmentVariablesDeletable;
  variable?: string;
}

export const EnvironmentVariableModal = (props: EnvironmentVariableModalProps) => {
  const { setVariables, variables, variable } = props;
  const { isOpen, onOpen, onClose } = useDisclosure();
  const isCreateMode = variable === undefined;
  const initialValues = {
    key: isCreateMode ? '' : variable,
    value: isCreateMode ? '' : variables[variable].value,
  };
  return (
    <>
      {isCreateMode ? (
        <Button colorScheme="blue" onClick={onOpen} size="sm">
          Add
        </Button>
      ) : (
        <Tooltip label="Edit variable">
          <Button variant="ghost" colorScheme="blue" onClick={onOpen}>
            <EditIcon />
          </Button>
        </Tooltip>
      )}
      <Modal size="3xl" isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {isCreateMode ? 'Create Environment Variable' : 'Update Environment Variable'}
          </ModalHeader>
          <Formik
            initialValues={initialValues}
            validationSchema={Yup.object({
              key: Yup.string()
                .matches(/^[_a-zA-Z][_a-zA-Z0-9]*$/, 'Invalid environment variable name')
                .notOneOf(
                  isCreateMode ? Object.keys(variables) : [],
                  'Environment variable name already exists'
                )
                .required('Required'),
              value: Yup.string().required('Required'),
            })}
            onSubmit={(values: any) => {
              setVariables({ ...variables, [values.key]: { value: values.value, delete: false } });
              onClose();
            }}
          >
            <Form>
              <ModalBody>
                <VStack width="full" spacing="6">
                  <Box w="full">
                    <InputControl name="key" label="Key" isReadOnly={!isCreateMode} />
                    <Text color="gray.500" mt={1} fontSize="xs">
                      <UnorderedList>
                        <ListItem>Alphanumeric (a-z, A-Z, 0-9) and underscores (_) only</ListItem>
                        <ListItem>Spaces are not allowed</ListItem>
                        <ListItem>Cannot start with a number</ListItem>
                      </UnorderedList>
                    </Text>
                  </Box>
                  <TextareaControl name="value" label="Value" />
                </VStack>
              </ModalBody>
              <ModalFooter>
                <Button colorScheme="blue" mr={3} type="submit">
                  {isCreateMode ? 'Add' : 'Save'}
                </Button>
                <Button variant="ghost" onClick={onClose}>
                  Cancel
                </Button>
              </ModalFooter>
            </Form>
          </Formik>
        </ModalContent>
      </Modal>
    </>
  );
};
