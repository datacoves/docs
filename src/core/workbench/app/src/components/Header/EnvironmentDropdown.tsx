/* eslint-disable jsx-a11y/no-autofocus */
import { ChevronDownIcon } from '@chakra-ui/icons';
import {
  Menu,
  MenuItem,
  MenuList,
  MenuGroup,
  MenuButton,
  Button,
  useColorModeValue as mode,
  Badge,
  Tooltip,
  Box,
  Input,
  InputGroup,
  InputLeftElement,
} from '@chakra-ui/react';
import { sum } from 'lodash';
import { useCallback, useContext, useMemo, useState } from 'react';
import { BsSearch } from 'react-icons/bs';

import { UserContext, GetEnvironmentNameAndSlug } from '../../context/UserContext';
import { Project } from '../../context/UserContext/types';
import { getSiteContext } from '../../utils/siteContext';

export const EnvironmentDropdown = () => {
  const { currentUser } = useContext(UserContext);
  const siteContext = getSiteContext();
  const { currentEnvName, currentEnvSlug } = GetEnvironmentNameAndSlug(currentUser);
  const [search, setSearch] = useState('');

  const totalEnvs = useMemo(
    () => sum(currentUser?.projects?.map(({ environments }) => environments.length)),
    [currentUser?.projects]
  );

  const isInSearch = useCallback(
    (text: string) => text.toLocaleLowerCase().includes(search.toLocaleLowerCase()),
    [search]
  );

  const getFilteredEnvs = useCallback(
    (project: Project) =>
      project.environments.filter((env) => isInSearch(env.name) || isInSearch(env.slug)),
    [isInSearch]
  );

  const filteredProjects = useMemo(
    () =>
      currentUser?.projects
        ?.filter(
          (project) =>
            getFilteredEnvs(project).length > 0 ||
            isInSearch(project.repository.git_url) ||
            isInSearch(project.name)
        )
        ?.sort((a, b) => a.name.localeCompare(b.name)),
    [currentUser?.projects, getFilteredEnvs, isInSearch]
  );

  return (
    <Menu>
      <MenuButton
        as={Button}
        fontWeight="light"
        colorScheme="black"
        rightIcon={<ChevronDownIcon />}
      >
        {currentEnvName}
        <Badge ml="2">{currentEnvSlug}</Badge>
      </MenuButton>
      <MenuList
        rounded="md"
        shadow="lg"
        color={mode('gray.600', 'inherit')}
        maxH={96}
        overflowY="auto"
        pb="1"
      >
        {totalEnvs >= 4 && (
          <Box p="2">
            <InputGroup>
              <InputLeftElement h="8" pointerEvents="none" color="gray.400">
                <BsSearch size="10" />
              </InputLeftElement>
              <Input
                size="sm"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search"
                autoFocus
              />
            </InputGroup>
          </Box>
        )}
        {filteredProjects?.map((project) => (
          <div key={project.id}>
            <MenuGroup
              fontSize="md"
              fontWeight={
                project.environments.some((environment) => environment.slug === siteContext.env)
                  ? 'semibold'
                  : 'normal'
              }
              title={project.name}
            >
              {(getFilteredEnvs(project).length ? getFilteredEnvs(project) : project.environments)
                ?.sort((a, b) => a.name.localeCompare(b.name))
                .map((env) => (
                  <MenuItem
                    key={env.id}
                    fontSize="sm"
                    onClick={() =>
                      (window.location.href = `https://${env.slug}.${siteContext.launchpadHost}`)
                    }
                  >
                    <Tooltip
                      label={`Open ${env.name} environment`}
                      placement="right"
                      hasArrow
                      bg="white"
                      color="black"
                      key={env.id}
                    >
                      <Box w="full" fontWeight={currentEnvSlug === env.slug ? 'bold' : 'normal'}>
                        {env.name}
                        <Badge ml="2" fontSize="0.7em" rounded="md" shadow="sm" bgColor="gray.300">
                          {env.slug.toUpperCase()}
                        </Badge>
                      </Box>
                    </Tooltip>
                  </MenuItem>
                ))}
            </MenuGroup>
          </div>
        ))}
      </MenuList>
    </Menu>
  );
};
