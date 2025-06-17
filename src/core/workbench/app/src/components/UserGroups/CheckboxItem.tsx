import { QuestionOutlineIcon } from '@chakra-ui/icons';
import { HStack, Tooltip, GridItemProps, GridItem } from '@chakra-ui/react';
import { CheckboxControl } from 'formik-chakra-ui';
import { ChangeEvent } from 'react';

import { Group } from '../../features/admin/groups/types';

import { generalGroups, labelGroup } from './utils';

interface Props {
  name: string;
  value: string;
  label: string;
  description: string;
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void;
  styleProps?: GridItemProps;
  isDisabled?: boolean;
}

interface GroupProps {
  group: Group;
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void;
  isDisabled?: boolean;
}

const CheckboxItem = ({
  name,
  value,
  label,
  description,
  onChange,
  styleProps,
  isDisabled,
}: Props) => {
  return (
    <GridItem alignItems="flex-start" {...(styleProps && { ...styleProps })}>
      <HStack alignItems="center" w="full">
        <CheckboxControl
          value={value}
          name={name}
          {...(onChange && { onChange })}
          isDisabled={isDisabled}
        >
          {label}
        </CheckboxControl>
        <Tooltip label={description}>
          <QuestionOutlineIcon aria-label="Help" cursor="help" pb={1} h={6} />
        </Tooltip>
      </HStack>
    </GridItem>
  );
};

export const GroupCheckboxItem = ({ group, onChange, isDisabled }: GroupProps) => {
  const label = labelGroup(group.extended_group.name);
  return (
    <CheckboxItem
      value={group.id.toString()}
      name="groups"
      label={label}
      description={group.extended_group.description}
      isDisabled={isDisabled}
      {...(onChange && { onChange })}
      {...(label == generalGroups.SysAdmin && { styleProps: { colStart: 2 } })}
      {...(label == generalGroups.Viewer && { styleProps: { colStart: 3 } })}
      {...(label == generalGroups.Developer && { styleProps: { colStart: 1 } })}
    />
  );
};

export default CheckboxItem;
