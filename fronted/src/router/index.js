import { createRouter, createWebHistory } from 'vue-router'
import TradingView  from '@/views/TradingView.vue'
import RankingView  from '@/views/RankingView.vue'
import ScreenerView from '@/views/ScreenerView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/',          redirect: '/trading' },
    { path: '/trading',  name: 'trading',  component: TradingView  },
    { path: '/ranking',  name: 'ranking',  component: RankingView  },
    { path: '/screener', name: 'screener', component: ScreenerView },
  ],
})

export default router
