import { InfoOutlineIcon } from '@chakra-ui/icons';
import {
  Heading,
  HStack,
  Icon,
  Input,
  InputGroup,
  InputLeftElement,
  Stack,
  Tooltip,
} from '@chakra-ui/react';
import { sum } from 'lodash';
import { ChangeEvent, useContext, useEffect, useCallback, useMemo, useState, useRef } from 'react';
import { BsSearch } from 'react-icons/bs';
import { FaFolder } from 'react-icons/fa';

import { Project, User } from '../../../context/UserContext/types';
import { EnvironmentCard } from '../components/EnvironmentCard';
import { WebSocketContext } from '../websocket/WebSocketContext';

interface Props {
  currentUser: User | undefined;
}

export const EnvironmentsStack = ({ currentUser }: Props) => {
  const { isWebSocketReady, sendMessageBySocket } = useContext(WebSocketContext);
  const socketAttempts = useRef(1);

  const [searchValue, setSearchValue] = useState<string>('');
  const projects = useMemo(
    () =>
      currentUser?.projects.sort((a, b) => {
        return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
      }),
    [currentUser?.projects]
  );

  const checkStatus = (attempt: number) => {
    const slugs =
      currentUser?.projects.flatMap((project) => project.environments.map((env) => env.slug)) || [];
    socketAttempts.current++;
    sendMessageBySocket({
      message_type: 'env.status',
      env_slugs: slugs.join(','),
      component: 'launchpad',
      attempt: attempt,
    });
  };

  useEffect(() => {
    if (isWebSocketReady && socketAttempts.current == 1) {
      checkStatus(1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isWebSocketReady]);

  const isInSearch = useCallback(
    (text: string) => text.toLocaleLowerCase().includes(searchValue.toLocaleLowerCase()),
    [searchValue]
  );

  const getFilteredEnvs = useCallback(
    (project: Project) =>
      project.environments.filter((env) => isInSearch(env.name) || isInSearch(env.slug)),
    [isInSearch]
  );

  const filteredProjects = useMemo(
    () =>
      projects?.filter(
        (project) =>
          getFilteredEnvs(project).length > 0 ||
          isInSearch(project.repository.git_url) ||
          isInSearch(project.name)
      ),
    [getFilteredEnvs, isInSearch, projects]
  );

  const totalEnvs = useMemo(
    () => sum(projects?.map(({ environments }) => environments.length)),
    [projects]
  );

  const onInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  };

  return (
    <Stack spacing="12" w="3xl" mx="auto !important">
      {totalEnvs >= 4 && (
        <InputGroup>
          <InputLeftElement pointerEvents="none" color="gray.400">
            <BsSearch />
          </InputLeftElement>
          <Input
            value={searchValue}
            type="search"
            background="white"
            placeholder="Search by environment, project or repository"
            onChange={onInputChange}
          />
        </InputGroup>
      )}

      {filteredProjects?.map((project) => (
        <Stack key={project.id} spacing="6">
          <HStack>
            <Icon as={FaFolder} color="blue.900" />
            <Heading textTransform="capitalize" size="md">
              {project.name}
            </Heading>
            <Tooltip label={project.repository.git_url}>
              <InfoOutlineIcon ml={2} />
            </Tooltip>
          </HStack>
          <Stack spacing="12">
            {(getFilteredEnvs(project).length ? getFilteredEnvs(project) : project.environments)
              .sort((a, b) => {
                return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
              })
              .map((environment) => (
                <EnvironmentCard key={environment.id} environment={environment} project={project} />
              ))}
          </Stack>
        </Stack>
      ))}
    </Stack>
  );
};
