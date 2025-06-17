import { ViewIcon } from '@chakra-ui/icons';
import { Link, Tooltip } from '@chakra-ui/react';
import React, { useContext } from 'react';

import { UserContext } from '../../context/UserContext';
import { getSiteContext } from '../../utils/siteContext';

export const GrafanaButton = () => {
  const siteContext = getSiteContext();
  const { currentUser } = useContext(UserContext);

  return (
    <>
      {currentUser &&
        currentUser?.features.observability_stack &&
        currentUser.permissions.find((permission) => permission.includes('services:grafana')) && (
          <Tooltip label="Services Metrics & Logs">
            <Link href={`https://grafana.${siteContext.launchpadHost}`} isExternal display="flex">
              <ViewIcon boxSize={5} mr={2} />
            </Link>
          </Tooltip>
        )}
    </>
  );
};
