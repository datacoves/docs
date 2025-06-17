import { Button } from '@chakra-ui/react';
import * as React from 'react';

import { AlertDialog } from '../../../components/AlertDialog';
import { useDeleteProfileSSHKey } from '../api/deleteProfileSSHKey';

export const DeleteProfileSSHKey = ({ id }: { id: string }) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const onClose = () => setIsOpen(false);
  const deleteMutation = useDeleteProfileSSHKey();
  const handleDelete = () => {
    deleteMutation.mutate(id);
  };

  return (
    <>
      <Button
        mt="5"
        size="sm"
        colorScheme="red"
        onClick={() => setIsOpen(true)}
        isLoading={deleteMutation.isLoading}
      >
        Delete key
      </Button>
      <AlertDialog
        isOpen={isOpen}
        header="Delete SSH key"
        message="Are you sure? You can't undo this action afterwards."
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleDelete}
      />
    </>
  );
};
