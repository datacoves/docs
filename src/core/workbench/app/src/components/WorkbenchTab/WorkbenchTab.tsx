import { Box } from '@chakra-ui/react';
import React, { useEffect, useContext, useState } from 'react';

import { TabsContext } from '../../context/TabsContext';

export function WorkbenchTab(props: any) {
  const { currentTab } = useContext(TabsContext);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (props.name === currentTab) {
      if (!props.isLoading && !loaded) {
        setLoaded(true);
      }
      if (props.isLoading && loaded) {
        setLoaded(false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentTab, props]);

  return (
    <Box display={props.name === currentTab ? 'block' : 'none'}>
      {props.sidebar}
      {loaded && (
        <iframe
          title={props.name}
          name={props.name}
          src={props.url}
          key={props.newkey || props.url}
          allowFullScreen
          allow="clipboard-read; clipboard-write"
          style={{
            height: '100vh',
            width: props.sidebar ? 'calc(100% - 95px)' : '100%',
            marginTop: '-48px',
            paddingTop: '48px',
          }}
        ></iframe>
      )}
    </Box>
  );
}
