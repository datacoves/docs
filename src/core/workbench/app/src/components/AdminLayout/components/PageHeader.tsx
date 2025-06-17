import { Box, Container, Heading, useColorModeValue } from '@chakra-ui/react';

export const PageHeader = (props: any) => (
  <Box bg={useColorModeValue('white', 'gray.900')} pt="5" shadow="sm" {...props}>
    <Container maxW="7xl">
      <Heading size="lg" mb="5">
        {props.header}
      </Heading>
    </Container>
  </Box>
);
