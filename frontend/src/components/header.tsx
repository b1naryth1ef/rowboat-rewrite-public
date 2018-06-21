import * as React from 'react';
import { store } from 'statorgfc';

import axios from 'axios';

import { API_ENDPOINT } from '../constants';


interface IHeaderState {
  user: any;
}

export default class Header extends React.Component<{}, IHeaderState> {
  constructor(props: any) {
    super(props);

    store.connectComponentState(this, ['user']);
  }

  public render() {
    return (
      <div className="header py-4">
        <div className="container">
          <div className="d-flex">
            <a className="header-brand" href="/">
              Rowboat
            </a>
            {this.state.user !== null && this.userDetails()}
          </div>
        </div>
      </div>
    );
  }

  private userDetails() {
    return (
      <div className="d-flex order-lg-2 ml-auto">
        <div className="nav-item d-none d-md-flex">
          <a className="btn btn-sm btn-outline-danger" onClick={this.logout}>Logout</a>
        </div>
        <div>
					<a href="#" className="nav-link pr-0 leading-none" data-toggle="dropdown">
            <img className="avatar" src={`${this.state.user.getAvatarURL()}`} />
						<span className="ml-2 d-none d-lg-block">
							<span className="text-default">{this.state.user.username}</span>
						</span>
					</a>
        </div>
      </div>
    );
  }

	private logout = async () => {
    await axios.post(`${API_ENDPOINT}/auth/logout`);
    window.location = window.location;
  }
}

