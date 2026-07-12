<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from './components/Navbar.vue'

const route = useRoute()
const router = useRouter()

// Mostrar Navbar en todas las rutas excepto login (/)
const showNavbar = computed(() => route.path !== '/')

function handleLogout() {
  router.push('/')
}

// Inicializar variable CSS por si no hay Navbar (evitar salto visual)
onMounted(() => {
  const saved = localStorage.getItem('cmms-sidebar-mode')
  if (saved === 'compact') {
    document.documentElement.style.setProperty('--sidebar-width', '60px')
  } else if (saved === 'expanded') {
    document.documentElement.style.setProperty('--sidebar-width', '250px')
  } else {
    document.documentElement.style.setProperty('--sidebar-width', '0px')
  }
})
</script>

<template>
  <div v-if="showNavbar" class="app-layout">
    <Navbar @logout="handleLogout" />
    <router-view />
  </div>
  <router-view v-else />
</template>

<style>
/* Estilos globales basicos */
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
  background-color: #f4f6f9;
}

/* Layout que se desplaza segun el ancho del sidebar */
.app-layout {
  margin-left: var(--sidebar-width, 0px);
  transition: margin-left 0.25s ease;
  min-height: 100vh;
}
</style>