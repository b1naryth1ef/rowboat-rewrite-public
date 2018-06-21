import * as Navigo from 'navigo';
import * as React from 'react';
import { store } from 'statorgfc';

import axios from 'axios';

import './assets/app.css';
import { DashboardPage } from './components/pages/dashboard';
import { GuildPage} from './components/pages/guild';
import { LoginPage } from './components/pages/login';
import { API_ENDPOINT } from './constants';
import { User } from './models/user';

interface IAppState {
  error: string | null;
  ready: boolean;
  routed: boolean;
  user: any;
  selectedGuild: any;
}

class App extends React.Component {
  public state: IAppState;
  private router: any;

  constructor(props: any) {
    super(props);

    this.initializeApplication();

    store.connectComponentState(this, ['user', 'ready', 'selectedGuild']);
    this.state.error = null;
    this.state.routed = false;

    this.router = new Navigo(window.location.origin, false);
  }

  public componentDidMount() {
    this.router.on('/guilds/:id', async (params: any) => {
      try {
        const res = await axios.get(`${API_ENDPOINT}/guilds/${params.id}`);
        this.setState({selectedGuild: res.data, routed: true});
      } catch (err) {
        if (err.response.status === 403) {
          this.setState({routed: true});
        } else {
          this.setState({error: err.message, routed: true});
        }
      }
    }).notFound(() => {
      this.setState({routed: true});
    }).resolve();
  }

  public render() {
    if (!this.state.ready || !this.state.routed) {
      return <div />;
    } else if (this.state.error !== null) {
      return <h1>Error: {this.state.error}</h1>;
    } else if (this.state.user === null) {
      return <LoginPage />;
    } else if (this.state.user !== null) {
      if (this.state.selectedGuild !== null) {
        return <GuildPage guild={this.state.selectedGuild} />;
      } else {
        return <DashboardPage />;
      }
    } else {
      return <h1>Error: unknown issue...</h1>;
    }
  }

  private async initializeApplication() {
    try {
      const res = await axios.get(`${API_ENDPOINT}/auth/@me`);
      const user = new User(res.data);
      store.set({user, ready: true});
    } catch (err) {
      // User isn't logged in
      if (err.response.status === 403) {
        store.set({ready: true});
      } else {
        store.set({ready: true});
        this.setState({error: err.message});
      }
    }
  }
}

export default App;
