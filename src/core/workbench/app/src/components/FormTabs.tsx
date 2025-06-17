import { ChevronDownIcon } from '@chakra-ui/icons';
import { Box, Collapse, Flex, Heading, Tab, TabList } from '@chakra-ui/react';
import * as React from 'react';
import { useState } from 'react';

interface FormTabsProps {
  labels: Array<string | { [key: string]: Array<any> }>;
  isSecondary?: boolean;
  activeTab?: number;
  startIndex?: number;
}

interface TabItemProps {
  label: string;
  isSecondary?: boolean;
  isDisabled?: boolean;
}

interface MenuSubitemProps {
  labels: { [key: string]: Array<any> };
  startIndex?: number;
  activeTab?: number;
}

export const FormTabs = (props: FormTabsProps) => {
  const { labels, isSecondary, activeTab, startIndex } = props;
  return (
    <TabList w="xs" {...(isSecondary && { border: 'none' })}>
      {labels.map((label, index) => (
        <React.Fragment key={`tab-${label}`}>
          {typeof label == 'string' ? (
            <TabItem
              isSecondary={isSecondary}
              label={label}
              {...(activeTab !== undefined && {
                isDisabled: index + (startIndex || 0) > activeTab,
              })}
            />
          ) : (
            typeof label == 'object' && (
              <MenuSubitem startIndex={index} activeTab={activeTab} labels={label} />
            )
          )}
        </React.Fragment>
      ))}
    </TabList>
  );
};

const TabItem = ({ label, isSecondary, isDisabled }: TabItemProps) => (
  <Tab
    key={`tab-${label}`}
    justifyContent="flex-start"
    textAlign="left"
    _selected={{ bg: 'gray.100', borderLeftColor: 'gray.200' }}
    p="4"
    fontWeight={isSecondary ? 'normal' : 'bold'}
    isDisabled={isDisabled}
  >
    {label}
  </Tab>
);

const MenuSubitem = ({ labels, startIndex, activeTab }: MenuSubitemProps) => {
  const [isActive, setIsActive] = useState(true);
  const label = Object.keys(labels)[0];
  const items = labels[label];
  return (
    <>
      <Flex
        onClick={() => setIsActive((prev) => !prev)}
        justifyContent="space-between"
        alignItems="center"
        p={4}
        cursor="pointer"
        {...(startIndex !== undefined &&
          activeTab !== undefined &&
          startIndex > activeTab && { opacity: 0.4 })}
      >
        <Heading size="sm">{label}</Heading>
        <ChevronDownIcon />
      </Flex>
      <Box pl={4}>
        <Collapse in={isActive}>
          <FormTabs activeTab={activeTab} startIndex={startIndex} isSecondary labels={items} />
        </Collapse>
      </Box>
    </>
  );
};
