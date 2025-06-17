import { Button, Stack, StackProps, Text } from '@chakra-ui/react';
import React, { useContext } from 'react';

import { AlertDialog } from '../../../../components/AlertDialog';
import { Card } from '../../../../components/Card';
import { HeadingGroup } from '../../../../components/ProfileForm/HeadingGroup';
import { AccountContext } from '../../../../context/AccountContext';
import { useDeleteAccount } from '../api/deleteAccount';

export const DangerZone = (props: StackProps) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const onClose = () => setIsOpen(false);
  const { currentAccount } = useContext(AccountContext);

  const deleteMutation = useDeleteAccount();
  const handleConfirmDelete = () => {
    if (currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
      });
    }
  };

  return (
    <Stack as="section" spacing="6" {...props}>
      <HeadingGroup title="Danger Zone" description="Irreversible and destructive actions" />
      <Card>
        <Text fontWeight="bold">Delete my account and data</Text>
        <Text fontSize="sm" mt="1" mb="3">
          Once you delete your account, there is no going back. Please be certain.
        </Text>
        <Button
          size="sm"
          colorScheme="red"
          isLoading={deleteMutation.isLoading}
          onClick={() => setIsOpen(true)}
        >
          Delete account
        </Button>
        <AlertDialog
          isOpen={isOpen}
          header="Delete account"
          message="Are you sure? You can't undo this action afterwards."
          confirmLabel="Delete"
          onClose={onClose}
          onConfirm={() => handleConfirmDelete()}
        />
      </Card>
    </Stack>
  );
};
