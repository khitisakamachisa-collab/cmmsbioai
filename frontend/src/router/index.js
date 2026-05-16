import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import OrdenesView from '../views/OrdenesView.vue' // <--- Importar nueva vista
import InventarioView from '../views/InventarioView.vue' // <--- Nuevo
import UsuariosView from '../views/UsuariosView.vue' // Importar
import PreventivoView from '../views/PreventivoView.vue' // <--- AGREGA ESTA LÍNEA


const routes = [
  {
    path: '/',
    name: 'login',
    component: LoginView
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView
  },
  {
    path: '/ordenes', // <--- Nueva Ruta
    name: 'ordenes',
    component: OrdenesView
  },
  {
    path: '/inventario',
    name: 'inventario',
    component: InventarioView
  },
  {
    path: '/usuarios',
    name: 'usuarios',
    component: UsuariosView
  },
  // ... dentro del array routes ...
  {
    path: '/preventivo',
    name: 'preventivo',
    component: PreventivoView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router