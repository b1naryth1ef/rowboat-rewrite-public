import * as React from 'react';

import GuildTable from '../guild_table';
import Page from '../page';

export class DashboardPage extends React.Component {
  public render() {
    return (
      <Page>
        <GuildTable />
      </Page>
    );
  }
}
