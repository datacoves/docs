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
  VStack,
} from '@chakra-ui/react';
import { Form, Formik } from 'formik';
import * as React from 'react';
import { RiAddFill } from 'react-icons/ri';
import * as Yup from 'yup';

import { FormikInput } from '../../../../components/Forms/FormikInput';

export const ModalAddPermission = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();

  return (
    <>
      <Button iconSpacing="1" onClick={onOpen} leftIcon={<RiAddFill fontSize="1.25em" />}>
        Add
      </Button>

      <Modal size="sm" isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Add permission</ModalHeader>
          <ModalCloseButton />
          <Formik
            initialValues={{ project: '', resource: '', action: '' }}
            validationSchema={Yup.object({
              project: Yup.string().required('Required'),
              resource: Yup.string().required('Required'),
              action: Yup.string().required('Required'),
            })}
            onSubmit={(val) => alert(JSON.stringify(val, null, 2))}
          >
            <Form>
              <ModalBody>
                <VStack width="full" spacing="6">
                  <FormikInput name="project" label="Project" />
                  <FormikInput name="resource" label="Resource" placeholder="example:example" />
                  <FormikInput name="action" label="Action" />
                </VStack>
              </ModalBody>
              <ModalFooter>
                <Button colorScheme="blue" mr={3} type="submit">
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
