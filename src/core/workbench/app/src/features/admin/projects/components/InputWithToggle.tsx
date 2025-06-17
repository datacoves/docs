import { FormControl, FormErrorMessage, FormLabel } from '@chakra-ui/form-control';
import { Input } from '@chakra-ui/input';
import { Box, Flex, Text } from '@chakra-ui/layout';
import { Switch } from '@chakra-ui/react';
import { useField } from 'formik';
import React, { FC, useEffect, useState } from 'react';

type NewType = JSX.IntrinsicElements['input'];

interface InputWithToggleProps extends NewType {
  label: string;
  name: string;
  stateValue?: boolean;
}

export const InputWithToggle: FC<InputWithToggleProps> = ({ label, stateValue, ...props }) => {
  const [field, meta] = useField(props);

  const [value, setValue] = useState(false);

  useEffect(() => {
    if (stateValue) {
      setValue(true);
    }
  }, [stateValue]);

  return (
    <FormControl isInvalid={meta.touched && !!meta.error}>
      <FormLabel id={`${props.id}-${props.name}-label`} htmlFor={`${props.id}-${props.name}-input`}>
        {label}
      </FormLabel>
      <Flex justify="space-between" alignItems="center" display="flex">
        <Input
          {...field}
          id={`${props.id}-${props.name}-input`}
          type="text"
          mr={5}
          isReadOnly={!value}
        />
        {meta.touched && meta.error ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
        <Box alignItems="center" display="flex" justifyContent="center" verticalAlign="baseline">
          <Switch
            id={`${props.id}-${props.name}-switch`}
            mr={1}
            display="flex"
            isChecked={value}
            onChange={() => setValue(!value)}
          />
          <Text>override</Text>
        </Box>
      </Flex>
    </FormControl>
  );
};
