import * as React from 'react';

import Header from './header';

export default class Page extends React.Component {
  public render() {
    return (
      <div>
        <Header />
        <div className="page">
          <div className="page-single">
            <div className="container">
              {this.props.children}
            </div>
          </div>
        </div>
      </div>
    );
  }
}
