import { createApp } from 'vue'
import { createStore } from 'vuex'
import './tailwind.css'
import App from './App.vue'
import { routes } from './routes.js'
import { createRouter, createWebHistory } from 'vue-router'
import axios from "axios";

axios.defaults.withCredentials = true
const api = axios.create({
  baseURL: "http://local.dev.com:8000/",
});

const app = createApp(App)

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const store = createStore({
  state () {
    return {
      user: {},
      isAuthenticated: false
    }
  },
  mutations: {
    saveUser (state, user) {
      state.user = user
      state.isAuthenticated = true
    },
    logout (state) {
      state.isAuthenticated = false
      state.user = {}
    },
  },
  actions: {
    loadUser(context) {
      api
        .get('users/me')
        .then((res) => {
          console.log(res.data)
          store.commit("saveUser", res.data)
        })
    },
  },
})
app.config.globalProperties.api=api
app.config.devtools = true
app.use(router)
app.use(store)
app.mount('#app')
