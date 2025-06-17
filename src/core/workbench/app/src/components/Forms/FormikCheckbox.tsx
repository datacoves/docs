import { FormControl, FormErrorMessage } from '@chakra-ui/form-control';
import { Checkbox, Text } from '@chakra-ui/react';
import { useField } from 'formik';
import React, { FC } from 'react';

type NewType = JSX.IntrinsicElements['input'];

interface ICustomFieldProps extends NewType {
  label?: string;
  name: string;
  value?: string;
  disabled?: boolean;
  hint?: string;
}

// TODO: Deprecated in favor of 'formik-chakra-ui'
export const FormikCheckbox: FC<ICustomFieldProps> = ({ label, ...props }) => {
  const [field, meta] = useField({ ...props, type: 'checkbox' });
  return (
    <FormControl isInvalid={meta.touched && !!meta.error}>
      <Checkbox pt={1} {...field} isDisabled={props.disabled}>
        {label}
      </Checkbox>
      <Text color="gray.500" fontSize="xs" pl={6}>
        {props.hint}
      </Text>
      {meta.touched && meta.error ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};
