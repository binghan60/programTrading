import http from './http'

export function fetchStrategies() {
  return http.get('/backtest/strategies').then(r => r.data)
}

export function runBacktest(payload, signal) {
  return http.post('/backtest/run', payload, { signal }).then(r => r.data)
}
