export type Label = string | null

declare module 'claude-code' {
  interface PluginState {
    'cache-timer': { label: Label }
  }
}
