import { Badge, Tooltip } from '@chakra-ui/react';
import React from 'react';

interface ProfileFileProps {
  filesCount: number;
}
export const ProfileFilesRow = (props: ProfileFileProps) => {
  const { filesCount } = props;
  return (
    <Tooltip hasArrow bg="gray.300" color="black">
      <Badge mx={1} fontSize="xs">
        {filesCount} code file{filesCount === 1 ? '' : 's'}
      </Badge>
    </Tooltip>
  );
};
