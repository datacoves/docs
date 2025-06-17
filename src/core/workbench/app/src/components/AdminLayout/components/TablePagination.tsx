import { Button, ButtonGroup, Flex, Text, useColorModeValue as mode } from '@chakra-ui/react';
import React from 'react';

interface TablePaginationProps {
  objectName: string;
  total?: number;
  prevLink?: string;
  prevHandler: () => void;
  nextLink?: string;
  nextHandler: () => void;
}

export const TablePagination = (props: TablePaginationProps) => {
  return (
    <Flex align="center" justify="space-between">
      <Text color={mode('gray.600', 'gray.400')} fontSize="sm">
        {props.total === 1 ? `1 ${props.objectName}` : `${props.total} ${props.objectName}s`}
      </Text>
      <ButtonGroup variant="outline" size="sm">
        <Button onClick={props.prevHandler} isDisabled={!props.prevLink}>
          Previous
        </Button>
        <Button onClick={props.nextHandler} isDisabled={!props.nextLink}>
          Next
        </Button>
      </ButtonGroup>
    </Flex>
  );
};
