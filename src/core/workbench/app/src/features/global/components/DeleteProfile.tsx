import { Button, Flex, Stack, StackProps, Text } from '@chakra-ui/react';
import * as React from 'react';

import { AlertDialog } from '../../../components/AlertDialog';
import { Card } from '../../../components/Card';
import { HeadingGroup } from '../../../components/ProfileForm/HeadingGroup';
import { useDeleteProfile } from '../api/deleteProfile';

export const DeleteProfile = (props: StackProps) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const onClose = () => setIsOpen(false);
  const deleteMutation = useDeleteProfile();

  const handleDelete = () => {
    deleteMutation.mutate();
  };

  return (
    <Stack as="section" spacing="6" {...props}>
      <HeadingGroup title="Danger Zone" description="Irreversible and destructive actions" />
      <Card>
        <Text fontWeight="bold">Delete my user account and data</Text>
        <Text fontSize="sm" mt="1" mb="3">
          Once you delete your user account, there is no going back. Please be certain.
        </Text>
        <Flex w="full" justifyContent="flex-end">
          <Button
            size="sm"
            colorScheme="red"
            onClick={() => setIsOpen(true)}
            isLoading={deleteMutation.isLoading}
          >
            Delete account
          </Button>
        </Flex>
        <AlertDialog
          isOpen={isOpen}
          header="Delete my user account"
          message="Are you sure? You can't undo this action afterwards."
          confirmLabel="Delete"
          onClose={onClose}
          onConfirm={handleDelete}
        />
      </Card>
    </Stack>
  );
};
