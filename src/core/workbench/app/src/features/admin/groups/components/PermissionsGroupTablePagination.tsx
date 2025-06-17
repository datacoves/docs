import { Button, ButtonGroup, Flex, Text, useColorModeValue as mode } from '@chakra-ui/react';
import React from 'react';

export const PermissionsGroupTablePagination = (props: any) => {
  if (!props.data) return null;

  return (
    <Flex align="center" justify="space-between">
      <Text color={mode('gray.600', 'gray.400')} fontSize="sm">
        {props.data.length === 1
          ? `${props.data.length} permission`
          : `${props.data.length} permissions`}
      </Text>
      {props.data.length > 16 && (
        <ButtonGroup variant="outline" size="sm">
          <Button as="a" rel="prev">
            Previous
          </Button>
          <Button as="a" rel="next">
            Next
          </Button>
        </ButtonGroup>
      )}
    </Flex>
  );
};
