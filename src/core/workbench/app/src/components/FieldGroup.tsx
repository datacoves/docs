import { Box, Heading, Stack, StackProps } from '@chakra-ui/react';
import * as React from 'react';

interface FieldGroupProps extends StackProps {
  title?: string;
  isTable?: boolean;
}

export const FieldGroup = (props: FieldGroupProps) => {
  const { title, isTable, children, ...flexProps } = props;
  return (
    <>
      {isTable ? (
        <Stack direction="column" spacing="6" py="4" {...flexProps}>
          <Box minW="3xs">
            {title && (
              <Heading as="h2" fontWeight="semibold" fontSize="lg" flexShrink={0}>
                {title}
              </Heading>
            )}
          </Box>
          {children}
        </Stack>
      ) : (
        <Stack
          direction={{ base: 'column', md: 'row' }}
          spacing="6"
          py="4"
          {...flexProps}
          // borderBottom="1px"
          // borderColor="whitesmoke"
        >
          <Box minW="3xs">
            {title && (
              <Heading as="h2" fontWeight="semibold" fontSize="lg" flexShrink={0}>
                {title}
              </Heading>
            )}
          </Box>
          {children}
        </Stack>
      )}
    </>
  );
};
