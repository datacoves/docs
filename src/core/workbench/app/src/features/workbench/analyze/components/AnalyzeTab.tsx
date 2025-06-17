import React from 'react';

import { WorkbenchTab } from '../../../../components/WorkbenchTab';
import { analyzeLink } from '../../../../utils/link';

export function AnalyzeTab({ isLoading }: { isLoading: boolean }) {
  return <WorkbenchTab name="analyze" url={analyzeLink()} isLoading={isLoading} />;
}
