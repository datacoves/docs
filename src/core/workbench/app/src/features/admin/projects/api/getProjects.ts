import { useQuery } from 'react-query';

import { Project } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';
// import { IAPIPaginatedResponse } from '../../../../types';

interface IGetProjects {
  account?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

// interface IProjectsResponse extends IAPIPaginatedResponse {
//   results: Project[];
// }

type ProjectsResponse = {
  count: number;
  next: string;
  previous: string;
  results: Project[];
};

export const getProjects = ({
  account,
  search,
  limit,
  offset,
}: IGetProjects): Promise<ProjectsResponse> => {
  const params = {
    search: search ? search : undefined,
    limit: limit ? limit : undefined,
    offset: offset ? offset : undefined,
  };
  return axios.get(`/api/admin/${account}/projects`, {
    params: params,
  });
};

export const useProjects = ({ account, search, limit, offset }: IGetProjects) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['projects', account, search, limit, offset],
    queryFn: () => getProjects({ account, search, limit, offset }),
  });
};

export const getAllProjects = ({ account }: { account?: string }): Promise<Project[]> => {
  // Returns all projects (without pagination)
  return axios.get(`/api/admin/${account}/projects`);
};

interface UseAllProjectsOptions {
  account?: string;
}

export const useAllProjects = ({ account }: UseAllProjectsOptions) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['projects', account],
    queryFn: () => getAllProjects({ account }),
  });
};
