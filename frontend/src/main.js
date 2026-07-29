import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // Importar router

const app = createApp(App)

app.use(router) // Usar router
app.mount('#app')