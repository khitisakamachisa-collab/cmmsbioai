<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'

const username = ref('')
const password = ref('')
const error_msg = ref('')
const router = useRouter()

const handleLogin = async () => {
  error_msg.value = ''
  try {
    // FastAPI espera datos como 'form-data' para OAuth2, no como JSON.
    // Creamos un objeto URLSearchParams para enviarlo correctamente.
    const formData = new URLSearchParams()
    formData.append('username', username.value)
    formData.append('password', password.value)

    // Llamamos a nuestro backend
    const response = await apiClient.post('/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })

    // Si todo sale bien, recibimos el token
    const token = response.data.access_token
    
    // Guardamos el token en localStorage (memoria del navegador)
    localStorage.setItem('token', token)
    
    // Redirigimos al Dashboard
    router.push('/dashboard')

  } catch (error) {
    if (error.response && error.response.status === 400) {
      error_msg.value = 'Usuario o contraseña incorrectos'
    } else {
      error_msg.value = 'Error de conexión con el servidor'
      console.error(error)
    }
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-box">
      <h2>CMMS-BioAI</h2>
      <p style="color: #666; font-size: 0.9rem;">Sistema de Mantenimiento</p>
      
      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <label>Usuario</label>
          <input v-model="username" type="text" placeholder="Ingrese usuario" required />
        </div>
        
        <div class="input-group">
          <label>Contraseña</label>
          <input v-model="password" type="password" placeholder="Ingrese contraseña" required />
        </div>

        <p v-if="error_msg" class="error">{{ error_msg }}</p>

        <button type="submit">Iniciar Sesión</button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}

.login-box {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.input-group {
  margin-bottom: 1rem;
  text-align: left;
}

.input-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  font-size: 0.9rem;
}

.input-group input {
  width: 100%;
  padding: 0.8rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box; /* Para que el padding no rompa el ancho */
}

button {
  width: 100%;
  padding: 0.8rem;
  background-color: #2c3e50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  margin-top: 1rem;
}

button:hover {
  background-color: #34495e;
}

.error {
  color: red;
  font-size: 0.85rem;
  margin-bottom: 1rem;
}
</style>