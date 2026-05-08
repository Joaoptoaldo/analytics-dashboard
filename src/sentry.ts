// @ts-nocheck
const dsn = import.meta.env.VITE_SENTRY_DSN || ""
if (dsn) {
  (async () => {
    try {
      const dynImport = new Function('p', 'return import(p)')
      const Sentry = await dynImport('@sentry/react')
      const Tracing = await dynImport('@sentry/tracing')
      Sentry.init({
        dsn,
        integrations: [new Tracing.BrowserTracing()],
        environment: import.meta.env.VITE_ENV || import.meta.env.MODE,
        release: import.meta.env.VITE_RELEASE || import.meta.env.npm_package_version,
        tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || 0),
        profilesSampleRate: Number(import.meta.env.VITE_SENTRY_PROFILES_SAMPLE_RATE || 0),
      })
      // export is not necessary for runtime usage
    } catch (e) {
      // ignore if packages not installed or import fails
      // console.warn('Sentry init failed', e)
    }
  })()
}

export default null
