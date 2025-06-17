import { WarningIcon } from '@chakra-ui/icons';
import { Tag, Tooltip } from '@chakra-ui/react';
import React, { useContext } from 'react';

import { UserContext } from '../../context/UserContext';

export const MissingDeveloperLicense = () => {
  const { currentUser } = useContext(UserContext);
  return (
    <>
      {currentUser && !currentUser?.has_license && (
        <Tooltip
          label="There are no available developer licenses, please contact your account administrator."
          hasArrow
          bg="white"
          color="black"
        >
          <Tag colorScheme="yellow">
            <WarningIcon mr="1" /> Missing Developer License
          </Tag>
        </Tooltip>
      )}
    </>
  );
};
