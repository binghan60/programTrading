import http from './http'

export function searchStocks(q = '') {
  return http.get('/stocks', { params: { q } }).then(r => r.data)
}

export function getKbars(code, start, end, signal) {
  return http.get(`/stocks/${code}/kbars`, { params: { start, end }, signal }).then(r => r.data)
}
