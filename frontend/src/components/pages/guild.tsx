import * as React from 'react';
import { store } from 'statorgfc';

import AceEditor from 'react-ace';
import 'brace/mode/yaml';
import 'brace/theme/tomorrow';

import axios from 'axios';

import { API_ENDPOINT } from '../../constants';
import Page from '../page';


class GuildStats extends React.Component {
  public props: {
    guild: any,
  };

  public render() {
    const stats = this.props.guild.stats;
    if (!stats) {
      return <div />;
    }

    return (
      <div className="row row-cards">
        {this.card('Members', stats.member_count)}
        {this.card('Channels', stats.channel_count)}
        {this.card('Roles', stats.role_count)}
        {this.card('Emoji', stats.emoji_count)}
      </div>
    );
  }

  private card(name: string, value: number) {
    return (
      <div className="col-6 col-sm-4 col-lg-3">
        <div className="card">
          <div className="card-body p-3 text-center">
            <div className="h1 m-0">{value}</div>
            <div className="text-muted mb-4">{name}</div>
          </div>
        </div>
      </div>
    );
  }
}


class GuildConfigEditor extends React.Component {
  public props: {
    guild: any,
    user: any,
  };

  public state: {
    contents: string | null,
    changed: boolean,
    saving: boolean,
    config: any,
    message: string | null,
  };

  constructor(props: any) {
    super(props);

    this.state = {
      changed: false,
      config: null,
      contents: null,
      message: null,
      saving: false,
    };
  }

  public async componentDidMount() {
    try {
      const res = await axios.get(`${API_ENDPOINT}/guilds/${this.props.guild.guild_id}/config`);
      this.setState({config: res.data, contents: res.data.contents});
    } catch (err) {
      console.error('Failed to load guild config: ', err);
    }
  }

  public render() {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Config</h3>
        </div>
        <div className="card-body">
          {this.body()}
        </div>
        <div className="card-footer">
          {this.footer()}
        </div>
      </div>
    );
  }

  private onClickSave = async () => {
    this.setState({saving: true, message: ''});
    try {
      const res = await axios.post(`${API_ENDPOINT}/guilds/${this.props.guild.guild_id}/config`, {
        contents: this.state.contents,
        previous_config_id: this.state.config.config_id,
      });
      this.setState({saving: false, config: res.data, message: 'Saved!', contents: res.data.contents});
    } catch (err) {
      console.error('Failed to save config: ', err);
      if (err.response.data && err.response.data.error) {
        this.setState({saving: false, message: err.response.data.error});
      }
    }
  }

  private footer() {
    if (this.state.config === null) {
      return <div />;
    }

    return (
      <div>
        <button
          className="btn btn-primary"
          onClick={this.onClickSave}
          disabled={!this.canEdit() || !this.state.changed}>
            Save
        </button>
        <p className="pull-right">{this.state.message || ''}</p>
      </div>
    );
  }

  private onEditorChange = (newValue: string) => {
    this.setState({contents: newValue, changed: true});
  }

  private body() {
    if (this.state.config === null) {
      return <p>Loading...</p>;
    }

    return <AceEditor
      mode="yaml"
      theme="tomorrow"
      width="100%"
      readOnly={this.state.saving}
      value={this.state.contents || ''}
      onChange={this.onEditorChange}
    />;
  }

  private canEdit() {
    const userID= this.props.user.id;
    return (
      this.props.user.admin ||
      this.props.guild.web.editors.includes(userID) ||
      this.props.guild.web.admins.includes(userID)
    );
  }
}

export class GuildPage extends React.Component {
  public props: {
    guild: any,
  };

  public state: {
    user: any,
  }

  constructor(props: any) {
    super(props);
    store.connectComponentState(this, ['user']);
  }

  public render() {
    const guild = this.props.guild;

    return (
      <Page>
        <div className="page-header">
          <h1 className="page-title">{guild.name}</h1>
        </div>
        <GuildStats guild={guild} />
        <GuildConfigEditor guild={guild} user={this.state.user} />
      </Page>
    );
  }
}
