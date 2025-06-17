import { BsEnvelope } from 'react-icons/bs';
import { FaConnectdevelop } from 'react-icons/fa';
import { HiOutlineKey, HiOutlineUserGroup } from 'react-icons/hi';
import { IconType } from 'react-icons/lib';
import { MdAttachMoney, MdCable, MdOutlineDashboard, MdOutlineLockOpen } from 'react-icons/md';
import { RiHomeGearLine, RiPlugLine, RiUser3Line, RiUserSettingsLine } from 'react-icons/ri';

import { Account } from '../../context/AccountContext/types';
import { User } from '../../context/UserContext/types';

export interface MenuSection {
  [key: string]: AccountItem[];
}

export interface AccountItem {
  shouldRender: boolean;
  heading: string;
  text: string;
  navigateTo: string;
  icon: IconType;
}

export const getAccountAdministrationMenu = (
  currentUser: User | undefined,
  currentAccount: Account | undefined
): MenuSection => ({
  'Users & Groups': [
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_groups &&
        currentUser.permissions.find((permission) => permission.includes('admin:groups|write'))
      ),
      heading: 'Groups',
      text: 'Add groups and manage permissions',
      navigateTo: '/admin/groups',
      icon: MdOutlineLockOpen,
    },
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_invitations &&
        currentUser.permissions.find((permission) => permission.includes('admin:invitations|write'))
      ),
      heading: 'Invitations',
      text: 'Invite users and manage access',
      navigateTo: '/admin/invitations',
      icon: BsEnvelope,
    },
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_users &&
        currentUser.permissions.find((permission) => permission.includes('admin:users|write'))
      ),
      heading: 'Users',
      text: 'Add users and assign groups',
      navigateTo: '/admin/users',
      icon: RiUser3Line,
    },
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_profiles &&
        currentUser.permissions.find((permission) => permission.includes('admin:profiles|write'))
      ),
      heading: 'Profiles',
      text: 'Configure and manage profiles',
      navigateTo: '/admin/profiles',
      icon: HiOutlineUserGroup,
    },
  ],
  'Projects & Environments': [
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_projects &&
        currentUser.permissions.find((permission) => permission.includes('admin:projects|write'))
      ),
      heading: 'Projects',
      text: 'Add and manage projects',
      navigateTo: '/admin/projects',
      icon: MdOutlineDashboard,
    },
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_environments &&
        currentUser.permissions.find((permission) =>
          permission.includes('admin:environments|write')
        )
      ),
      heading: 'Environments',
      text: 'Configure and manage environments',
      navigateTo: '/admin/environments',
      icon: RiHomeGearLine,
    },
  ],
  Credentials: [
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_connections &&
        currentUser.permissions.find((permission) =>
          permission.includes('admin:connectiontemplates|write')
        )
      ),
      heading: 'Connection templates',
      text: 'Configure default connection templates',
      navigateTo: '/admin/connection-templates',
      icon: MdCable,
    },
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_service_credentials &&
        currentUser.permissions.find((permission) =>
          permission.includes('admin:servicecredentials|write')
        )
      ),
      heading: 'Service connections',
      text: 'Configure services connections',
      navigateTo: '/admin/service-connections',
      icon: RiPlugLine,
    },
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_integrations &&
        currentUser.permissions.find((permission) =>
          permission.includes('admin:integrations|write')
        )
      ),
      heading: 'Integrations',
      text: 'Configure integrations',
      navigateTo: '/admin/integrations',
      icon: FaConnectdevelop,
    },
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_secrets &&
        currentUser.permissions.find((permission) => permission.includes('admin:secrets|write'))
      ),
      heading: 'Secrets',
      text: 'Configure secrets',
      navigateTo: '/admin/secrets',
      icon: HiOutlineKey,
    },
  ],
  'Account & Billing': [
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_account &&
        currentAccount?.owned_by === currentUser.email &&
        !currentUser?.features.accounts_signup
      ),
      heading: 'Account settings',
      text: 'Change account global settings',
      navigateTo: '/admin/account',
      icon: RiUserSettingsLine,
    },
    {
      shouldRender: !!(
        currentUser &&
        currentUser?.features.admin_account &&
        currentAccount?.owned_by === currentUser.email &&
        currentUser?.features.accounts_signup
      ),
      heading: 'Account settings & billing',
      text: 'Change account billing and settings',
      navigateTo: '/admin/account',
      icon: MdAttachMoney,
    },
  ],
});
