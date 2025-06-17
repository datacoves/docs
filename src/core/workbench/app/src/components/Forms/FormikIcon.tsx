import { FormControl, FormErrorMessage, FormLabel } from '@chakra-ui/form-control';
import { StarIcon } from '@chakra-ui/icons';
import { Box, Input, Stack, Text } from '@chakra-ui/react';
import { useField } from 'formik';
import { FC } from 'react';

type NewType = JSX.IntrinsicElements['input'];

interface ICustomFieldProps extends NewType {
  label?: string;
  name: string;
  value?: string;
  icon?: string;
  hint?: string;
}

// TODO: Deprecated in favor of 'formik-chakra-ui'
export const FormikIcon: FC<ICustomFieldProps> = ({ label, ...props }) => {
  const [field, meta] = useField(props);

  return (
    <FormControl isInvalid={meta.touched && !!meta.error}>
      <FormLabel htmlFor={props.id || props.name}>{label}</FormLabel>
      <Stack direction="row" spacing="12px" display="flex" alignItems="center">
        <StarIcon mx="2px" boxSize={6} />
        <Input {...field} isReadOnly value={props.value} id={props.id || props.name} />
      </Stack>
      <Box>
        {props.hint && (
          <Text color="gray.500" mt={1}>
            {props.hint}
          </Text>
        )}
        {meta.touched && meta.error ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
      </Box>
    </FormControl>
  );
};
