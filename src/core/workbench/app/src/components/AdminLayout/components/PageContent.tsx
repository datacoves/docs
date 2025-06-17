import { Box, Container, useColorModeValue } from '@chakra-ui/react';

export const PageContent = (props: any) => {
  return (
    <Box as="main" flex="1" {...props}>
      <Container maxW="7xl">
        <Box bg={useColorModeValue('white', 'gray.700')} p="6" rounded="lg" shadow="base">
          {props.children}
        </Box>
      </Container>
    </Box>
  );
};
