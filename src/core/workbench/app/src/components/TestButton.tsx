import { CheckIcon } from '@chakra-ui/icons';
import { Box, Button, ButtonProps, Tooltip } from '@chakra-ui/react';
import { formatRelative, parseISO } from 'date-fns';
import { MdFlashOn } from 'react-icons/md';

interface TestButtonProps extends ButtonProps {
  testType: string;
  validatedAt: string | undefined;
}

export const TestButton = ({ testType, validatedAt, ...buttonProps }: TestButtonProps) => {
  const tested = !!validatedAt;
  return (
    <Tooltip
      label={
        tested
          ? `Last validated at ${formatRelative(parseISO(validatedAt), new Date())}`
          : `Test ${testType}`
      }
    >
      <Button
        variant={tested ? 'ghost' : 'solid'}
        colorScheme={tested ? 'green' : 'blue'}
        size="sm"
        minW="24"
        leftIcon={tested ? <CheckIcon /> : <MdFlashOn />}
        loadingText="Testing"
        borderWidth="1px"
        borderColor={tested ? 'green.500' : 'blue.500'}
        {...buttonProps}
      >
        <Box pt="2px">{tested ? 'Re-test' : 'Test'}</Box>
      </Button>
    </Tooltip>
  );
};
