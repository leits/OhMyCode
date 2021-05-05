<template>
  <main class="h-screen">
    <nav class="bg-white py-2 md:py-4">
    <div class="container px-4 mx-auto md:flex md:items-center">

      <div class="flex justify-between items-center">
        <!-- <a href="#" class="font-bold text-xl text-indigo-600">OhMyCode</a> -->
        <router-link
              to="/"
              class="font-bold text-xl text-indigo-600"
              >OhMyCode</router-link
            >
        <button class="border border-solid border-gray-600 px-3 py-1 rounded text-gray-600 opacity-50 hover:opacity-75 md:hidden" id="navbar-toggle">
          <i class="fas fa-bars"></i>
        </button>
      </div>
      <User />
    </div>
  </nav>
    <router-view />
  </main>
</template>

<script>
import { defineComponent } from 'vue'
import User from '@/components/User.vue'

export default defineComponent({
  components: { User },
})
</script>