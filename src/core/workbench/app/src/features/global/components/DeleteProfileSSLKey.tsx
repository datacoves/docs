import { Button } from '@chakra-ui/react';
import * as React from 'react';

import { AlertDialog } from '../../../components/AlertDialog';
import { useDeleteProfileSSLKey } from '../api/deleteProfileSSLKey';

export const DeleteProfileSSLKey = ({ id }: { id: string }) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const onClose = () => setIsOpen(false);
  const deleteMutation = useDeleteProfileSSLKey();
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
        header="Delete SSL key"
        message="Are you sure? You can't undo this action afterwards."
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleDelete}
      />
    </>
  );
};
