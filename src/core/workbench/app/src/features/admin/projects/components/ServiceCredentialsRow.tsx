import { Badge, Link, Tooltip } from '@chakra-ui/react';
import React from 'react';
import { useNavigate } from 'react-router-dom';

interface CredentialProps {
  credsCount: number;
  environmentId: string;
}
export const ServiceCredentialsRow = (props: CredentialProps) => {
  const { credsCount, environmentId } = props;
  const navigate = useNavigate();
  return (
    <Tooltip hasArrow label="Manage service connections" bg="gray.300" color="black">
      <Link
        onClick={() => {
          navigate(`/admin/service-connections?environmentId=${environmentId}`);
        }}
      >
        <Badge mx={1} fontSize="xs">
          {credsCount} service connection{credsCount === 1 ? '' : 's'}
        </Badge>
      </Link>
    </Tooltip>
  );
};
