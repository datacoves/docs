import { FormControl, FormLabel, FormErrorMessage } from '@chakra-ui/form-control';
import { Select } from '@chakra-ui/select';
import { useField } from 'formik';
import React, { FC } from 'react';

type NewType = JSX.IntrinsicElements['input'];

interface ICustomFieldProps extends NewType {
  label?: string;
  name: string;
}

// TODO: Deprecated in favor of 'formik-chakra-ui'
export const FormikSelect: FC<ICustomFieldProps> = ({ label, ...props }) => {
  const [field, meta] = useField(props);

  return (
    <FormControl isInvalid={meta.touched && !!meta.error}>
      <FormLabel htmlFor={props.id || props.name}>{label}</FormLabel>
      <Select {...field} id={props.id || props.name}>
        {props.children}
      </Select>
      {meta.touched && meta.error ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};
