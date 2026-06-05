export function useAutoSave(options = {}) {
  const {
    saveFn,
    getPayload,
    debounceMs = 1000,
    intervalMs = 30000
  } = options

  let debounceTimer = null
  let intervalTimer = null
  let saving = false

  async function doSave(trigger) {
    if (saving) return
    if (typeof saveFn !== 'function') return
    const payload = typeof getPayload === 'function' ? getPayload(trigger) : undefined
    saving = true
    try {
      await saveFn(payload, trigger)
    } finally {
      saving = false
    }
  }

  function scheduleDebouncedSave(trigger) {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    debounceTimer = setTimeout(() => {
      debounceTimer = null
      doSave(trigger)
    }, debounceMs)
  }

  function startInterval() {
    stopInterval()
    intervalTimer = setInterval(() => doSave('interval'), intervalMs)
  }

  function stopInterval() {
    if (intervalTimer) {
      clearInterval(intervalTimer)
      intervalTimer = null
    }
  }

  function dispose() {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    stopInterval()
  }

  return {
    doSave,
    scheduleDebouncedSave,
    startInterval,
    stopInterval,
    dispose
  }
}

