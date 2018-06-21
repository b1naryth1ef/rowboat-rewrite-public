import * as React from 'react';

import Page from '../page';

export class LoginPage extends React.Component {
  public render() {
    return (
      <Page>
        <div className="row">
          <div className="col col-login mx-auto">
            <form className="card" action="" method="post">
              <div className="card-body p-6">
                <div className="card-title">Login to your account</div>
                <div className="form-group">
                  <a href="http://localhost:45000/api/auth/discord">
                    <img src="https://discordapp.com/assets/bb408e0343ddedc0967f246f7e89cebf.svg" height="128" width="256" style={{
                      display: 'block',
                      margin: 'auto',
                    }} />
                  </a>
                </div>
              </div>
            </form>
            <div className="text-center text-muted">
              Don't have Rowboat setup yet? Add it to your server <a href="...">here</a>!
            </div>
          </div>
        </div>
      </Page>
    );
  }
}
