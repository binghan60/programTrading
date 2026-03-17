import { createApp } from 'vue'
import { createPinia } from 'pinia'
import VueVirtualScroller from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(VueVirtualScroller)

// 全域未捕獲錯誤統一送至 notify store
app.config.errorHandler = (err) => {
  import('@/stores/notify').then(({ useNotifyStore }) => {
    useNotifyStore().error(err?.message ?? '發生未知錯誤')
  })
  console.error('[errorHandler]', err)
}

app.mount('#app')
