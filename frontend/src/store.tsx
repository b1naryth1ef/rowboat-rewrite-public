import { store } from 'statorgfc';

export function initialize() {
  store.initialize({
    // Dictates whether the app is "ready" (e.g. we know whether we are logged in or not)
    ready: false,

    // The currently selected guild
    selectedGuild: null,

    // The logged in user
    user: null,
  });
}
