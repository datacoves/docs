import { Box, Container } from '@chakra-ui/react';
import React from 'react';

export const PageContentNoBox = (props: any) => {
  return (
    <Box as="main" py="8" flex="1" {...props}>
      <Container maxW="7xl">
        <Box bg="gray.100" p="6">
          {props.children}
        </Box>
      </Container>
    </Box>
  );
};
