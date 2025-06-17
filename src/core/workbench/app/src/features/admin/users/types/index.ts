export type UserGroup = {
  id: number;
  name: string;
};

export type User = {
  name: string;
  email: string;
  groups: UserGroup[];
  id: string;
  last_login?: string;
};
