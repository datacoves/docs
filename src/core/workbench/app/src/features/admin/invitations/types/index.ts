export type InvitationGroup = {
  id: number;
  name: string;
};

export type Invitation = {
  name: string;
  email: string;
  groups: InvitationGroup[];
  id: string;
  status: string;
};
