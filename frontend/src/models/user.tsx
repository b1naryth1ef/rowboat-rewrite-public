export class User {
  public id: string;
  public username: string;
  public discriminator: number;
  public avatarHash: string;
  public admin: boolean;

  constructor(payload: any) {
    this.id = payload.id;
    this.username = payload.username;
    this.discriminator = payload.discriminator;
    this.avatarHash = payload.avatar;
    this.admin = payload.admin;
  }

  public getAvatarURL(size?: number) {
    return `https://cdn.discordapp.com/avatars/${this.id}/${this.avatarHash}.png?size=${size || 128}`;
  }
}
