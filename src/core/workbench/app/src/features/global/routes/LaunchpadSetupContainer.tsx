import { Stack, Button, VStack, Text, Box, Alert, AlertIcon } from '@chakra-ui/react';
import { useState } from 'react';
import { useNavigate } from 'react-router';

import { Account } from '../../../context/AccountContext/types';
import { User } from '../../../context/UserContext/types';
import { notifySetupRequest } from '../api/notifySetupRequest';

interface LaunchpadSetupContainerProps {
  account: Account | undefined;
  user: User;
  contact: () => void;
}

export const LaunchpadSetupContainer: React.FC<LaunchpadSetupContainerProps> = ({
  account,
  user,
  contact,
}) => {
  const navigate = useNavigate();
  const [setupDisabled, setSetupDisabled] = useState<boolean>(false);
  const [setupRequestSent, setSetupRequestSent] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const handleSetupRequest = async (user: User) => {
    if (user.setup_enabled === true) {
      navigate('/account-setup');
    } else {
      setLoading(true);
      await notifySetupRequest();
      setSetupDisabled(true);
      setSetupRequestSent(true);
      setLoading(false);
    }
  };
  return (
    <VStack spacing={10}>
      <Stack spacing="3" direction={{ base: 'column', sm: 'row' }} justify="center">
        <Button onClick={contact}>Contact sales</Button>
        <Button
          colorScheme="blue"
          onClick={() => handleSetupRequest(user)}
          isDisabled={user.setup_enabled === false || setupDisabled}
          isLoading={loading}
        >
          {account?.owned_by === user.email || user.setup_enabled
            ? 'Continue account setup'
            : 'Create new account'}
        </Button>
      </Stack>
      {(setupRequestSent || user.setup_enabled === false) && (
        <Box>
          <Alert status="info" variant="left-accent">
            <AlertIcon />
            <Stack direction="column" spacing={1}>
              <Text>We&apos;re glad you want to create a trial account</Text>
              <Text>Let&apos;s make sure you have a smooth onboarding experience.</Text>
              <Text>We will contact you shortly to get you all set up</Text>
            </Stack>
          </Alert>
        </Box>
      )}
    </VStack>
  );
};
