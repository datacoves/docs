import { axios } from '../../../../lib/axios';
import { WorkbenchStatus } from '../types';

export const getWorkbenchStatus = (envSlug: string | undefined): Promise<WorkbenchStatus> => {
  return axios.get(`api/workbench/${envSlug}/status`);
};
