import { ExternalLinkIcon } from '@chakra-ui/icons';
import { Box, Stack, Link, Tooltip } from '@chakra-ui/react';

interface ProjectProps {
  name: string;
  url: string;
}
export const ProjectsRow = (props: ProjectProps) => {
  const { name, url } = props;
  const link = 'https://' + url.replace('git@', '').replace(':', '/');
  return (
    <Stack direction="row" spacing="4" align="center" maxW="330px">
      <Box overflow="hidden">
        <Box fontSize="sm" fontWeight="medium" overflow="hidden">
          {name}
        </Box>
        <Tooltip label={link}>
          <Box fontSize="sm" color="gray.500" isTruncated={true}>
            <Link href={link} isExternal>
              {url}
              <ExternalLinkIcon mx="2px" />
            </Link>
          </Box>
        </Tooltip>
      </Box>
    </Stack>
  );
};
