
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_USE_EXTERNAL?: string;
  readonly VITE_EXTERNAL_SYNC_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
