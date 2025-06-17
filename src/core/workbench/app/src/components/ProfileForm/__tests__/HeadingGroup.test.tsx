import { screen, rtlRender, waitFor } from '../../../test/test-utils';
import { HeadingGroup } from '../HeadingGroup';

const title = 'Account Settings';
const description = 'Change account details.';

jest.mock('@chakra-ui/react', () => {
  const originalModule = jest.requireActual('@chakra-ui/react');
  return {
    __esModule: true,
    ...originalModule,
    useBreakpointValue: jest.fn().mockImplementation(() => false),
  };
});

describe('HeadingGroup Tests', () => {
  test('should handle basic HeadingGroup flow', async () => {
    const headingGroup = <HeadingGroup title={title} description={description} />;
    rtlRender(headingGroup);
    expect(screen.getByText(title)).toBeInTheDocument();
    await waitFor(() => expect(document.title).toEqual(''));
  });
});
