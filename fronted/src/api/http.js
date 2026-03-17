import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  timeout: 30000,
})

http.interceptors.response.use(
  res => res,
  err => {
    // 主動取消的請求（AbortController）不顯示錯誤
    if (axios.isCancel(err) || err.name === 'CanceledError') {
      return Promise.reject(err)
    }
    // 動態取得 notify store（確保 Pinia 已完成初始化）
    import('@/stores/notify').then(({ useNotifyStore }) => {
      const msg = err.response?.data?.detail ?? err.message ?? '請求失敗'
      useNotifyStore().error(msg)
    })
    return Promise.reject(err)
  }
)

export default http
