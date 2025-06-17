import { FormControl, FormLabel } from '@chakra-ui/form-control';
import { ExternalLinkIcon } from '@chakra-ui/icons';
import { Button, Stack, Link } from '@chakra-ui/react';
import { useField } from 'formik';
import { FC } from 'react';

type NewType = JSX.IntrinsicElements['input'];

interface ICustomFieldProps extends NewType {
  label: string;
  name: string;
  link: string;
}

// TODO: Deprecated in favor of 'formik-chakra-ui'
export const FormikLink: FC<ICustomFieldProps> = ({ label, ...props }) => {
  const [, meta] = useField(props);

  return (
    <FormControl isInvalid={meta.touched && !!meta.error}>
      <FormLabel htmlFor={props.id || props.name}>{label}</FormLabel>
      <Stack
        direction={['column', 'row']}
        spacing="12px"
        display="flex"
        alignItems="center"
        justifyContent="space-around"
      >
        <Link href="#" color="blue" isExternal id={props.id || props.name}>
          {props.link}
          <ExternalLinkIcon mx="2px" />
        </Link>
        <Button w={{ base: 'full', md: 'auto' }}>Set Up</Button>
      </Stack>
    </FormControl>
  );
};
