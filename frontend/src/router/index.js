import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import HomeDashboard from '../views/HomeDashboard.vue'
import EquiposView from '../views/EquiposView.vue'
import OrdenesView from '../views/OrdenesView.vue'
import InventarioView from '../views/InventarioView.vue'
import UsuariosView from '../views/UsuariosView.vue'
import PreventivoView from '../views/PreventivoView.vue'
import HistorialView from '../views/HistorialView.vue'
import ReportesView from '../views/ReportesView.vue'


const routes = [
  {
    path: '/',
    name: 'login',
    component: LoginView
  },
  {
    path: '/inicio',
    name: 'inicio',
    component: HomeDashboard
  },
  {
    path: '/equipos',
    name: 'equipos',
    component: EquiposView
  },
  {
    path: '/ordenes',
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
  {
    path: '/preventivo',
    name: 'preventivo',
    component: PreventivoView
  },
  {
    path: '/historial',
    name: 'historial',
    component: HistorialView
  },
  {
    path: '/reportes',
    name: 'reportes',
    component: ReportesView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
