import {
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Heading,
} from '@chakra-ui/react';
import { groupBy, isArray } from 'lodash';
import { ReactNode } from 'react';

import { Permission } from '../types';

import PermissionCheckbox from './PermissionCheckbox';

interface Props {
  title: string;
  permissions: Array<Permission> | undefined;
  disabled?: boolean;
  children?: ReactNode;
}

const PermissionsAccordion = ({ title, permissions, disabled = false, children }: Props) => {
  const grouppedPermissions = isArray(permissions)
    ? groupBy(permissions, (i) => `${i.scope}-${i.resource}`)
    : {};
  return (
    <AccordionItem>
      <AccordionButton justifyContent="space-between">
        <Heading size="sm">{title}</Heading>
        <AccordionIcon />
      </AccordionButton>
      <AccordionPanel>
        {Object.keys(grouppedPermissions).map((key) => (
          <PermissionCheckbox
            key={`permission.${grouppedPermissions[key][0].id}`}
            permission={grouppedPermissions[key]}
            disabled={disabled}
          />
        ))}
        {children}
      </AccordionPanel>
    </AccordionItem>
  );
};

export default PermissionsAccordion;
