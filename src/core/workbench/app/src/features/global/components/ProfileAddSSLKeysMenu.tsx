import {
  Button,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  MenuList,
  Text,
  MenuItem,
} from '@chakra-ui/react';
import { Form, Formik } from 'formik';
import { TextareaControl } from 'formik-chakra-ui';
import * as React from 'react';
import * as Yup from 'yup';

import { useCreateProfileSSLKeys } from '../api/createProfileSSLKeys';

export const ProfileAddSSLKeysMenu = ({ handleGenerate }: { handleGenerate: () => void }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();

  const createMutation = useCreateProfileSSLKeys(onClose);

  const handleSubmit = (body: any, { setSubmitting }: any) => {
    createMutation.mutate(body.privateKey);
    setSubmitting(false);
  };
  return (
    <>
      <MenuList>
        <MenuItem onClick={() => handleGenerate()}>Auto-generate key pairs</MenuItem>
        <MenuItem onClick={onOpen}>Provide private key</MenuItem>
      </MenuList>
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Provide private PEM key</ModalHeader>
          <ModalCloseButton />
          <Formik
            initialValues={{ private: '' }}
            validationSchema={Yup.object({
              privateKey: Yup.string().required('Required'),
            })}
            onSubmit={handleSubmit}
          >
            <Form>
              <ModalBody>
                <TextareaControl name="privateKey" label="Private key" isRequired />
                <Text color="gray.500" mt={1} fontSize="xs">
                  Paste your private PEM key here.
                </Text>
              </ModalBody>
              <ModalFooter>
                <Button
                  colorScheme="blue"
                  mr={3}
                  type="submit"
                  isLoading={createMutation.isLoading}
                >
                  Save
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
