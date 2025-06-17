import { screen, rtlRender } from '../../../test/test-utils';
import { QuickLink } from '../QuickLink';

jest.mock('@chakra-ui/react', () => {
  const originalModule = jest.requireActual('@chakra-ui/react');
  return {
    __esModule: true,
    ...originalModule,
    useBreakpointValue: jest.fn().mockImplementation(() => false),
  };
});

describe('QuickLinks Tests', () => {
  test('should handle basic QuickLinks flow', () => {
    rtlRender(<QuickLink title="text" />);
    expect(screen.getByText('text')).toBeInTheDocument();
  });
});
