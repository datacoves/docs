import { FormControl, FormLabel, FormErrorMessage } from '@chakra-ui/form-control';
import { InfoIcon } from '@chakra-ui/icons';
import { Button, Flex, HStack, Tooltip, useToast } from '@chakra-ui/react';
import { useField } from 'formik';
import { TextareaControl } from 'formik-chakra-ui';
import { FC, useState, createElement } from 'react';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';

type NewType = JSX.IntrinsicElements['input'];

interface ICustomFieldProps extends NewType {
  label?: string;
  name: string;
  placeholder?: string;
  readonly?: boolean;
}

export const GitRepositorySignUpTextArea: FC<ICustomFieldProps> = ({ label, ...props }) => {
  const [field, meta] = useField(props);
  const [value, setValue] = useState<string>('');
  const toast = useToast();
  const handleInputChange = (e: any) => {
    const inputValue = e.target.value;
    setValue(inputValue);
  };
  const copyToClipboard = () => {
    navigator.clipboard.writeText({ value }.value);
    toast({
      render: () => {
        return createElement(ExpandibleToast, {
          message: 'SSH development key copied to clipboard',
          status: 'success',
        });
      },
      duration: 3000,
      isClosable: true,
    });
  };
  return (
    <FormControl isInvalid={meta.touched && !!meta.error}>
      <Flex justifyContent="space-between">
        <HStack alignItems="flex-start">
          <FormLabel
            id={`${props.id}-${props.name}-label`}
            htmlFor={`${props.id}-${props.name}-input`}
          >
            {label}
          </FormLabel>
          <Button colorScheme="gray" size="xs" onClick={copyToClipboard} alignSelf="baseline">
            Copy
          </Button>
        </HStack>
        <Tooltip
          hasArrow
          label="Copy and add this SSH key to your user account in your git tool (Github, Gitlab, Bitbucket)."
          bg="gray.300"
          color="black"
        >
          <InfoIcon boxSize={6} color="blue.500" />
        </Tooltip>
      </Flex>
      {props.readonly ? (
        <TextareaControl
          {...field}
          id={`${props.id}-${props.name}-textarea`}
          placeholder={props.placeholder}
          onChange={handleInputChange}
          isReadOnly
        />
      ) : (
        <TextareaControl
          {...field}
          id={`${props.id}-${props.name}-textarea`}
          placeholder={props.placeholder}
          onChange={handleInputChange}
        />
      )}
      {meta.touched && meta.error ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};
