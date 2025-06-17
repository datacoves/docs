import React, { useContext } from 'react';

import { WorkbenchTab } from '../../../../components/WorkbenchTab';
import { UserContext } from '../../../../context/UserContext';
import { transformLink } from '../../../../utils/link';

export function TransformTab({ isLoading }: { isLoading: boolean }) {
  const { currentUser } = useContext(UserContext);

  const link = currentUser ? transformLink(currentUser.slug) : undefined;

  return currentUser ? (
    <WorkbenchTab name="transform" url={link} isLoading={isLoading} />
  ) : (
    <div></div>
  );
}
