import * as React from 'react';
import * as ReactDOM from 'react-dom';
import App from './App';
import { initialize } from './store';

initialize();

ReactDOM.render(
  <App />,
  document.getElementById('root') as HTMLElement
);
