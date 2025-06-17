export interface IAPIPaginatedResponse {
  count: number;
  next: string;
  previous: string;
}

export type BaseEntity = {
  createdAt: number;
};

export enum WorkbenchTabType {
  Home,
  Load,
  Transform,
  Observe,
  Analyze,
}
