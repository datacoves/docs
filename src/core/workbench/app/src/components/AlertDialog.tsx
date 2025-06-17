import {
  Button,
  AlertDialog as AlertDialogChakra,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
} from '@chakra-ui/react';
import * as React from 'react';
import { useState } from 'react';

type IAlertDialogProps = {
  isOpen: boolean;
  header: string;
  message: any;
  confirmLabel: string;
  onClose: () => void;
  onConfirm?: () => void;
  isLoadingOnSubmit?: boolean;
  confirmColor?: string;
};
export const AlertDialog = ({
  isOpen,
  header,
  message,
  confirmLabel,
  onClose,
  onConfirm,
  isLoadingOnSubmit = false,
  confirmColor = 'red',
}: IAlertDialogProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const onSubmit = () => {
    if (isLoadingOnSubmit) {
      setIsSubmitting(true);
      onConfirm?.();
    } else {
      onClose();
      onConfirm?.();
    }
  };
  const cancelRef = React.useRef() as React.MutableRefObject<HTMLButtonElement>;

  return (
    <AlertDialogChakra isOpen={isOpen} leastDestructiveRef={cancelRef} onClose={onClose}>
      <AlertDialogOverlay>
        <AlertDialogContent>
          <AlertDialogHeader fontSize="lg" fontWeight="bold">
            {header}
          </AlertDialogHeader>

          <AlertDialogBody>{message}</AlertDialogBody>

          <AlertDialogFooter>
            <Button ref={cancelRef} onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button colorScheme={confirmColor} onClick={onSubmit} ml={3} isLoading={isSubmitting}>
              {confirmLabel}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialogOverlay>
    </AlertDialogChakra>
  );
};
