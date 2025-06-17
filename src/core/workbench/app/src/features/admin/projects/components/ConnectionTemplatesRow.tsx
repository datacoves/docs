import { Badge, Link, Tooltip } from '@chakra-ui/react';
import React from 'react';
import { useNavigate } from 'react-router-dom';

interface ConnProps {
  conns: string[];
  projectName: string;
  projectId: string;
}
export const ConnectionTemplatesRow = (props: ConnProps) => {
  const { conns, projectId } = props;
  const navigate = useNavigate();
  return (
    <Tooltip hasArrow label="Manage connection templates" bg="gray.300" color="black">
      <Link
        onClick={() => {
          navigate(`/admin/connection-templates?projectId=${projectId}`);
        }}
      >
        <Badge mx={1} fontSize="xs">
          {conns?.length} connection template{conns?.length > 1 ? 's' : ''}
        </Badge>
      </Link>
    </Tooltip>
  );
};
