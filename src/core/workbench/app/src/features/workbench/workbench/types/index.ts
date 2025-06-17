import { createContext } from 'react';

export type WorkbenchStatus = {
  status: string;
  services: {
    [key: string]: string;
  };
  containers: {
    [key: string]: [any];
  };
  updated_at: number;
  progress: number;
};

export type WorkbenchStatus2 = {
  env: string;
  details: WorkbenchStatus;
};

export interface IEnvStatus {
  status: Array<WorkbenchStatus2>;
  setStatus: (status: Array<WorkbenchStatus2>) => void;
}

export const EnvStatusContext = createContext<IEnvStatus>({
  status: new Array<WorkbenchStatus2>(),
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setStatus: (status: Array<WorkbenchStatus2>) => {},
});
