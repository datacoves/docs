import { InfoIcon, CheckCircleIcon } from '@chakra-ui/icons';
import { Text, HStack, Stack, Progress, Icon } from '@chakra-ui/react';
import React, { FC } from 'react';

interface ITestConnectionProgress {
  infoText: string;
  success?: boolean;
}
export const TestConnectionProgress: FC<ITestConnectionProgress> = ({ infoText, success }) => {
  return (
    <Stack width="full" spacing="6" mt={5}>
      {success === true ? (
        <>
          <Text align="center" fontSize="xl">
            Connection succesful!
          </Text>
          <Icon alignSelf="center" boxSize={10} color="green" as={CheckCircleIcon} />
        </>
      ) : (
        <>
          <Text align="center" fontSize="xl">
            Testing connection...
          </Text>
          <Progress size="xs" isIndeterminate />
        </>
      )}
      <HStack>
        <Icon boxSize={5} as={InfoIcon} />
        <Text>{infoText}</Text>
      </HStack>
    </Stack>
  );
};
