import { chakra, ImageProps, forwardRef } from '@chakra-ui/react';
import React from 'react';

import animatedLogo from '../assets/animated_logo_no_bg_small_200_15fps.gif';

export const DatacovesSpinner = forwardRef<ImageProps, 'img'>((props, ref) => {
  return <chakra.img src={animatedLogo} ref={ref} {...props} w={32} />;
});
