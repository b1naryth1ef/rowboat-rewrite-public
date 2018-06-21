import * as React from 'react';

import axios from 'axios';
import { API_ENDPOINT } from '../constants';


class GuildTableBody extends React.Component {
  public props: {
    guilds: any;
  };

  public render() {
    if (this.props.guilds === null) {
      return <h1>Loading...</h1>;
    }

    const guilds = [];

    for (const guild of this.props.guilds) {
      guilds.push(this.renderRow(guild));
    }
    return guilds;
  }

  private renderRow(guild: any) {
    return (
      <tr key={guild.guild_id}>
        <td>{guild.guild_id}</td>
        <td>{guild.name}</td>
        <td>
          <a href={`/guilds/${guild.guild_id}`} className="icon">
            <i className="fe fe-edit" />
          </a>
        </td>
      </tr>
    );
  }
}


export default class GuildTable extends React.Component {
  public state: {
    guilds: any;
  };

  constructor(props: any) {
    super(props);
    this.state = {guilds: null};
  }

  public async componentDidMount() {
    try {
      const res = await axios.get(`${API_ENDPOINT}/guilds`);
      this.setState({guilds: res.data});
    } catch (err) {
      console.error('Failed to get user guilds:', err);
    }
  }

	public render() {
    return (
      <div className="col-12">
        <div className="card">
          {this.state.guilds === null ? this.renderLoader() : this.renderTable()}
        </div>
      </div>
    );
  }

  private renderLoader() {
    return (
      <div className="card-body">
        <div className="dimmer active">
          <div className="loader" />
        </div>
      </div>
    );
  }

  private renderTable() {
    return (
      <div className="table-responsive">
        <table className="table table-hover table-outline table-vcenter text-nowrap card-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <GuildTableBody guilds={this.state.guilds} />
          </tbody>
        </table>
      </div>
    );
  }
}
