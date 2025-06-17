import { Center } from '@chakra-ui/layout';
import { Spinner } from '@chakra-ui/spinner';
import { ReactNode } from 'react';

interface Props {
  isLoading: boolean;
  showElements?: boolean;
  children: ReactNode;
}

export const LoadingWrapper = ({ isLoading, children, showElements = true }: Props) => (
  <>
    {isLoading || !showElements ? (
      <Center minHeight="50vh" w="full">
        <Spinner size="xl" color="blue" />
      </Center>
    ) : (
      showElements && children
    )}
  </>
);
