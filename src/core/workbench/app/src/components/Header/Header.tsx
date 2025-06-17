import { Flex, HStack, Box, Tooltip, Select, Text } from '@chakra-ui/react';
import { useContext } from 'react';

import { AccountContext } from '../../context/AccountContext';
import { Account } from '../../context/AccountContext/types';
import { TabsContext } from '../../context/TabsContext';
import { UserContext } from '../../context/UserContext';
import { WorkbenchStatus } from '../../features/workbench/workbench';
import { getSiteContext } from '../../utils/siteContext';
import { Logo } from '../Icons/Logo';

import { EnvironmentDropdown } from './EnvironmentDropdown';
import { FreeTrialButton } from './FreeTrial';
import { GrafanaButton } from './GrafanaButton';
import { MissingDeveloperLicense } from './MissingDeveloperLicense';
import { NavMenu } from './NavMenu';
import { ProfileDropdown } from './ProfileDropdown';

export function Header(props: { isWorkbench?: boolean; wstatus?: WorkbenchStatus }) {
  const { isWorkbench, wstatus } = props;
  const { currentTab } = useContext(TabsContext);
  const { accounts, currentAccount, setCurrentAccount } = useContext(AccountContext);
  const { currentUser } = useContext(UserContext);

  const bg = `${currentTab}.header`;
  const dark = ['docs', 'load', 'transform', 'observe', 'orchestrate'].includes(currentTab);
  const siteContext = getSiteContext();
  const logoUrl = currentUser?.env_account
    ? `https://${siteContext.launchpadHost}?account=${currentAccount?.slug}`
    : `https://${siteContext.launchpadHost}`;

  const onSelectAccount = (event: any) => {
    const account = accounts?.find((account: Account) => account.slug === event.target.value);
    setCurrentAccount(account);
  };

  return (
    <Flex
      align="center"
      zIndex="10"
      bg={bg}
      color="white"
      px="6"
      minH="12"
      position="fixed"
      w="100%"
    >
      <Flex justify="space-between" align="center" w="full">
        <Flex flexBasis="100%">
          {/* Desktop Logo placement */}
          <Flex alignItems="center">
            <Tooltip label="Go to Launchpad" placement="right" hasArrow bg="white" color="black">
              <Box href={logoUrl} id="logo-button" as="a" justifyContent="flex-start">
                <Logo display={{ base: 'none', lg: 'block' }} flexShrink={0} h="6" w="auto" />
              </Box>
            </Tooltip>
          </Flex>

          {!isWorkbench && accounts && (
            <HStack flex="1" display={{ base: 'none', lg: 'flex' }} justifyContent="flex-start">
              {accounts.length > 1 && (
                <Select
                  placeholder="Select account"
                  ml="5"
                  w="200"
                  border="none"
                  title="Select account"
                  value={currentAccount?.slug}
                  onChange={onSelectAccount}
                >
                  {[...accounts]
                    .sort((a, b) => {
                      return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
                    })
                    .map((account: Account) => (
                      <option color="black" key={account.slug} value={account.slug}>
                        {account.name}
                      </option>
                    ))}
                </Select>
              )}
              {accounts.length === 1 && (
                <Text ml="5" title="Account">
                  {currentAccount?.name}
                </Text>
              )}
            </HStack>
          )}

          {isWorkbench && currentUser?.projects && <EnvironmentDropdown />}
        </Flex>
        <Flex flexBasis="100%">
          {/* Desktop Navigation Menu */}
          {isWorkbench && <NavMenu.Desktop dark={dark} wstatus={wstatus} />}

          {/* Mobile Logo placement */}
          <Logo flex={{ base: '1', lg: '0' }} display={{ lg: 'none' }} flexShrink={0} h="5" />
        </Flex>
        <HStack spacing="3" minW="118px" justifyContent="flex-end" flexBasis="100%">
          <FreeTrialButton isWorkbench={isWorkbench} />
          <MissingDeveloperLicense />
          {!isWorkbench && <GrafanaButton />}
          <ProfileDropdown />
        </HStack>
      </Flex>
    </Flex>
  );
}
