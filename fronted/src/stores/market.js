import { defineStore } from 'pinia'
import { ref } from 'vue'
import { searchStocks } from '@/api/stocks'
import http from '@/api/http'

export const useMarketStore = defineStore('market', () => {
  const stocks = ref([])
  const selectedStock = ref(null)
  const query = ref('')
  const loading = ref(false)
  const isScreening = ref(false)

  // K 線資料快取（code → rows[]），純 Map 不需要響應式
  const kbarCache = new Map()

  let timer = null

  async function fetchStocks(q = '') {
    loading.value = true
    isScreening.value = false
    try {
      const list = await searchStocks(q)
      stocks.value = list
    } catch (err) {
      console.error('Failed to fetch stocks:', err)
    } finally {
      loading.value = false
    }
  }

  async function screenUptrend() {
    loading.value = true
    isScreening.value = true
    query.value = ''
    try {
      const response = await http.get('/stocks/screener/uptrend')
      stocks.value = response.data
    } catch (err) {
      console.error('Failed to screen uptrend:', err)
    } finally {
      loading.value = false
    }
  }

  function onSearchInput() {
    clearTimeout(timer)
    timer = setTimeout(() => {
      fetchStocks(query.value)
    }, 300)
  }

  function selectStock(stock) {
    selectedStock.value = stock
  }

  return {
    stocks,
    selectedStock,
    query,
    loading,
    isScreening,
    kbarCache,
    fetchStocks,
    onSearchInput,
    selectStock,
    screenUptrend,
  }
})
