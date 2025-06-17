import { FormControl, FormErrorMessage, FormLabel } from '@chakra-ui/form-control';
import { Box, Input, Text } from '@chakra-ui/react';
import { useField } from 'formik';
import React, { FC } from 'react';

type NewType = JSX.IntrinsicElements['input'];

interface ICustomFieldProps extends NewType {
  label?: string;
  name: string;
  type?: string;
  value?: string;
  readonly?: boolean;
  hint?: string;
  placeholder?: string;
}

// TODO: Deprecated in favor of 'formik-chakra-ui'
export const FormikInput: FC<ICustomFieldProps> = ({ label, ...props }) => {
  const [field, meta] = useField(props);

  return (
    <FormControl isInvalid={meta.touched && !!meta.error}>
      <FormLabel htmlFor={props.id || props.name}>{label}</FormLabel>
      <Box>
        <Input
          {...field}
          id={props.id || props.name}
          type={props.type}
          isReadOnly={props.readOnly}
          placeholder={props.placeholder}
        />
        {props.hint && (
          <Text color="gray.500" mt={1} fontSize="xs">
            {props.hint}
          </Text>
        )}
        {meta.touched && meta.error ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
      </Box>
    </FormControl>
  );
};
