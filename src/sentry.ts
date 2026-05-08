const dsn = import.meta.env.VITE_SENTRY_DSN || ""

type SentryModule = {
  init: (options: Record<string, unknown>) => void
}

type TracingModule = {
  BrowserTracing: new () => unknown
}

if (dsn) {
  (async () => {
    try {
      const dynImport = new Function('p', 'return import(p)')
      const Sentry = await dynImport('@sentry/react') as SentryModule
      const Tracing = await dynImport('@sentry/tracing') as TracingModule
      Sentry.init({
        dsn,
        integrations: [new Tracing.BrowserTracing()],
        environment: import.meta.env.VITE_ENV || import.meta.env.MODE,
        release: import.meta.env.VITE_RELEASE || import.meta.env.npm_package_version,
        tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || 0),
        profilesSampleRate: Number(import.meta.env.VITE_SENTRY_PROFILES_SAMPLE_RATE || 0),
      })
      // export is not necessary for runtime usage
    } catch {
      // ignore if packages not installed or import fails
    }
  })()
}

export default null
