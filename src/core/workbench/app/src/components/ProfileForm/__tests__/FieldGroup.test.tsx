import { screen, rtlRender, waitFor } from '../../../test/test-utils';
import { FieldGroup } from '../FieldGroup';

const title = 'Name';
const description = 'Change account name';

jest.mock('@chakra-ui/react', () => {
  const originalModule = jest.requireActual('@chakra-ui/react');
  return {
    __esModule: true,
    ...originalModule,
    useBreakpointValue: jest.fn().mockImplementation(() => false),
  };
});

describe('FieldGroup Tests', () => {
  test('should handle basic FieldGroup flow', async () => {
    const fieldGroup = <FieldGroup title={title} description={description} />;
    rtlRender(fieldGroup);
    expect(screen.getByText(title)).toBeInTheDocument();
    await waitFor(() => expect(document.title).toEqual(''));
  });
});
