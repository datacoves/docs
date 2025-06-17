import { Badge, Link, Tooltip } from '@chakra-ui/react';
import React from 'react';
import { useNavigate } from 'react-router-dom';

interface EnvProps {
  envs: string[];
  projectName: string;
  projectId: string;
}
export const EnvironmentsRow = (props: EnvProps) => {
  const { envs, projectId } = props;
  const navigate = useNavigate();
  return (
    <Tooltip hasArrow label="Manage environments" bg="gray.300" color="black">
      <Link
        onClick={() => {
          navigate(`/admin/environments?projectId=${projectId}`);
        }}
      >
        <Badge mx={1} fontSize="xs">
          {envs?.length} environment{envs?.length > 1 ? 's' : ''}
        </Badge>
      </Link>
    </Tooltip>
  );
};
