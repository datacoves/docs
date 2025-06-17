import { Box, StackProps, Text, VStack } from '@chakra-ui/layout';
import {
  Button,
  Input,
  Modal,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Textarea,
} from '@chakra-ui/react';
import { isObject, replace } from 'lodash';
import { ChangeEvent, useState } from 'react';
import { BsPlusCircle } from 'react-icons/bs';

import { SecretValueInput } from './SecretValueInput';

interface Props {
  values: { [key: string]: any };
  setFieldValue: (field: string, value: any, shouldValidate?: boolean | undefined) => void;
  initialKey?: string;
  styles?: StackProps;
}

export const EditSecretValues = (props: Props) => {
  return (
    <>
      <SecretValueSection {...props} styles={{ pl: 6 }} />
      <AddButton setFieldValue={props.setFieldValue} keyName={'value'} />
    </>
  );
};

const SecretValueSection = ({ values, setFieldValue, initialKey = 'value', styles }: Props) => {
  return (
    <>
      {Object.keys(values).map((key) => (
        <VStack w="full" key={key} {...(styles && { ...styles })} spacing={3}>
          {isObject(values[key]) ? (
            <>
              <SecretValueSection
                values={values[key]}
                setFieldValue={setFieldValue}
                initialKey={`${initialKey}.${key}`}
                styles={{ pl: 6 }}
              />
              <AddButton setFieldValue={setFieldValue} keyName={`${initialKey}.${key}`} />
            </>
          ) : (
            <SecretValueInput
              initialKey={initialKey}
              keyName={key}
              setFieldValue={setFieldValue}
              initialValue={values[key]}
            />
          )}
        </VStack>
      ))}
    </>
  );
};

interface AddButtonProps {
  setFieldValue: (field: string, value: any, shouldValidate?: boolean | undefined) => void;
  keyName: string;
}

const AddButton = ({ setFieldValue, keyName: key }: AddButtonProps) => {
  const [isModalOpen, setModalIsOpen] = useState(false);
  const [selectedKey, setSelectedKey] = useState<string>();
  const [modalForm, setModalForm] = useState({ key: '', value: '' });

  const onCloseModal = () => {
    setModalIsOpen(false);
  };

  const openFieldModal = (key: string) => {
    setModalIsOpen(true);
    setSelectedKey(key);
  };

  const formatJsonOrString = (text: string) => {
    try {
      return JSON.parse(text);
    } catch (e) {
      return text;
    }
  };

  const addField = () => {
    setFieldValue(`${selectedKey}.${modalForm.key}`, formatJsonOrString(modalForm.value));
    setModalForm({ key: '', value: '' });
    onCloseModal();
  };
  return (
    <>
      <Modal size="lg" isOpen={isModalOpen} onClose={onCloseModal}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Add new key</ModalHeader>
          <ModalCloseButton />
          <VStack p={8}>
            <Text fontSize="md" w="full">
              Secret Key
            </Text>
            <Input
              name="secretKey"
              placeholder="Secret Key"
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                setModalForm({ ...modalForm, key: e.target.value })
              }
            />
            <Text fontSize="md" w="full" pt="6">
              Secret Value
            </Text>
            <Textarea
              name="secretValue"
              placeholder="Secret Value"
              onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                setModalForm({ ...modalForm, value: e.target.value })
              }
            />
          </VStack>
          <Button onClick={() => addField()} colorScheme="blue">
            Add
          </Button>
        </ModalContent>
      </Modal>
      <Box pl={6} w="full">
        <Button
          gap={4}
          alignItems="center"
          alignSelf="flex-start"
          onClick={() => openFieldModal(key)}
        >
          <BsPlusCircle />
          {`Add Item ${key !== 'value' ? `in "${replace(key, 'value.', '')}"` : ''}`}
        </Button>
      </Box>
    </>
  );
};
