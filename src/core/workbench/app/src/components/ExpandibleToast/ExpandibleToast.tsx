import { Box, Text, Collapse, Button, HStack } from '@chakra-ui/react';
import { useState } from 'react';
import { AiOutlineCheckCircle, AiOutlineWarning, AiOutlineExclamationCircle } from 'react-icons/ai';

type ToastStatus = 'info' | 'success' | 'warning' | 'error';

interface CustomToastProps {
  message: string;
  extra?: string;
  status?: ToastStatus;
}

const statusColors = {
  info: 'blue.500',
  success: 'green.500',
  warning: 'orange.500',
  error: 'red.500',
};

const statusBgColors = {
  info: 'blue.50',
  success: 'green.50',
  warning: 'orange.50',
  error: 'red.50',
};

const statusIcons = {
  info: <AiOutlineCheckCircle size="12px" color="blue" />,
  success: <AiOutlineCheckCircle size="12px" color="green" />,
  warning: <AiOutlineWarning size="12px" color="orange" />,
  error: <AiOutlineExclamationCircle size="12px" color="red" />,
};

const ExpandibleToast: React.FC<CustomToastProps> = ({ message, extra, status = 'info' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const toggle = () => setIsOpen(!isOpen);

  return (
    <Box
      p={4}
      borderWidth="1px"
      borderRadius="md"
      boxShadow="md"
      bg="white"
      maxW="xl"
      // bg={statusColors[status]}
    >
      <HStack spacing={1}>
        {statusIcons[status]} {/* Dynamically render the icon based on status */}
        <Text fontWeight="bold" color={statusColors[status]}>
          {message}
        </Text>
      </HStack>
      {extra && (
        <>
          <Button size="sm" mt={2} onClick={toggle} variant="link" color={statusColors[status]}>
            {isOpen ? 'Hide Details' : 'Show Details'}
          </Button>
          <Collapse in={isOpen} animateOpacity>
            <Box mt={2} p={2} bg={statusBgColors[status]} borderRadius="md">
              <Text fontSize="sm">{extra}</Text>
            </Box>
          </Collapse>
        </>
      )}
    </Box>
  );
};

export default ExpandibleToast;
