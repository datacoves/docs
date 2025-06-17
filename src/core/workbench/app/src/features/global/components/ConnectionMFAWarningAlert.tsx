import { Alert, AlertIcon } from '@chakra-ui/react';
import React from 'react';

const ConnectionMFAWarningAlert: React.FC = () => {
  return (
    <Alert status="info">
      <AlertIcon />
      Please approve the connection test via your MFA application.
    </Alert>
  );
};

export default ConnectionMFAWarningAlert;
