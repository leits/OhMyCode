<script>
import { mapState } from "vuex";
import axios from "axios";
import { useStore, mapMutations } from 'vuex'

export default {
  name: "app",
  data() {
    return {};
  },
  setup(props, context) {
    const store = useStore()
    store.dispatch("loadUser");
  },
  computed: {
    ...mapState(["user"]),
    ...mapState(["isAuthenticated"]),
  },
  methods: {
    ...mapMutations(['logout']),
    login() {
      axios
        .get('http://local.dev.com:8000/auth/github/authorize?authentication_backend=cookie')
        .then((res) => {
          window.location.href = res.data.authorization_url
        })
    },
  }
};
</script>

<template>
  <div class="hidden md:flex flex-col md:flex-row md:ml-auto mt-3 md:mt-0" id="navbar-collapse">
    <div v-if="this.isAuthenticated" class="flex">
      <div class="flex-2 space-x-2">
        <router-link to="/dashboard">
          <button class="p-1 lg:px-4 md:mx-2 border border-solid border-indigo-600 rounded text-white bg-indigo-600 transition-colors duration-300 mt-1 md:mt-0 md:ml-1">
            <div class="flex">
              <div class="flex-1">
                <img class="rounded-full border border-gray-100 shadow-sm w-8 h-8" :src="this.user.avatar_url" alt="user image" />
              </div>
              <div class="flex-1 p-1">
                <p>Dashboard</p>
              </div>
            </div>
          </button>
        </router-link>
      </div>
      <div class="flex-1 space-x-2">
        <button v-on:click="logout" class="p-2 lg:px-4 md:mx-2 text-indigo-600 text-center border border-solid border-indigo-600 rounded hover:bg-indigo-600 hover:text-white transition-colors duration-300 mt-1 md:mt-0 md:ml-1">Logout</button>
      </div>
    </div>
    <div v-else>
      <button v-on:click="login" class="p-2 lg:px-4 md:mx-2 text-indigo-600 text-center border border-solid border-indigo-600 rounded hover:bg-indigo-600 hover:text-white transition-colors duration-300 mt-1 md:mt-0 md:ml-1">Login with GitHub</button>
    </div>
  </div>
</template>

