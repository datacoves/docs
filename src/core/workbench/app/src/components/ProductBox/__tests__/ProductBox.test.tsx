import { screen, rtlRender, waitFor, act } from '../../../test/test-utils';
import { ProductBox } from '../ProductBox';

// const text = `Documentation`;
const url = '';
const title = 'Bring your data together';
const subtitle = 'Powered by AirByte';
const text = 'Extract and load data from a variety of sources and keep the data synchronized.';
const button = 'Load';

jest.mock('@chakra-ui/react', () => {
  const originalModule = jest.requireActual('@chakra-ui/react');
  return {
    __esModule: true,
    ...originalModule,
    useBreakpointValue: jest.fn().mockImplementation(() => false),
  };
});

describe('ProductBox Tests', () => {
  test('should handle basic ProductBox flow', async () => {
    const productBox = (
      <ProductBox
        url={url}
        title={title}
        subtitle={subtitle}
        text={text}
        button={button}
        onClick={() => console.log('Load')}
      />
    );
    act(() => {
      rtlRender(productBox);
    });
    expect(screen.getByText(title)).toBeInTheDocument();
    await waitFor(() => expect(document.title).toEqual(''));
    // await waitFor(() => expect(screen.queryByText(title)).not.toBeInTheDocument());
  });
});
