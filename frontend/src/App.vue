<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from './components/Navbar.vue'

const route = useRoute()
const router = useRouter()

// Mostrar Navbar en todas las rutas excepto login (/)
const showNavbar = computed(() => route.path !== '/')

function handleLogout() {
  router.push('/')
}
</script>

<template>
  <Navbar v-if="showNavbar" @logout="handleLogout" />
  <router-view />
</template>

<style>
/* Estilos globales básicos */
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
  background-color: #f4f6f9;
}
</style>