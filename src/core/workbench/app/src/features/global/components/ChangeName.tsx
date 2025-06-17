import {
  Button,
  FormControl,
  FormLabel,
  Input,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
} from '@chakra-ui/react';
import * as React from 'react';

// import { useDisclosure } from '@/hooks/useDisclosure';
import { useDisclosure } from '../../../hooks/useDisclosure';

export const ChangeName = function () {
  const { isOpen, open, close } = useDisclosure();
  /// FIXME: not sure about the Element
  // const initialRef = React.useRef() as React.MutableRefObject<HTMLInputElement>;
  const initialRef = React.useRef<HTMLInputElement>(null);

  return (
    <>
      <Button size="sm" fontWeight="normal" onClick={open}>
        Change name
      </Button>
      <Modal initialFocusRef={initialRef} isOpen={isOpen} onClose={close}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Change your name</ModalHeader>
          <ModalCloseButton />s
          <ModalBody pb={6}>
            <FormControl>
              <FormLabel>First name</FormLabel>
              <Input ref={initialRef} placeholder="First name" />
            </FormControl>

            <FormControl mt={4}>
              <FormLabel>Last name</FormLabel>
              <Input placeholder="Last name" />
            </FormControl>
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" mr={3}>
              Save
            </Button>
            <Button onClick={close}>Cancel</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};
