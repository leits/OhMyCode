<script>
import axios from "axios";
import Multiselect from '@vueform/multiselect'

export default {
  name: "app",
  components: {
    Multiselect,
  },
  data() {
    return {
      value: null,
      options: [],
      repos: {}
    };
  },
  mounted() {
    axios
      .get('http://local.dev.com:8000/repos')
      .then((res) => {
        this.repos = res.data
        this.options = []
        res.data.forEach(repo => {
          this.options.push({'label': `${repo.owner}/${repo.name}`, 'value':repo.id})
        })
      })
  },
};
</script>

<template>
  <main>
    <div class="bg-gray-50">
      <div
        class="max-w-screen-xl px-4 py-12 mx-auto sm:px-6 lg:py-16 lg:px-8 lg:flex lg:items-center lg:justify-between"
      >
        <h2
          class="text-3xl font-extrabold leading-9 tracking-tight text-gray-900 sm:text-4xl sm:leading-10"
        >
          Dashboard
        </h2>
      </div>
    </div>
    <div class="bg-gray-50 flex flex-wrap overflow-hidden">

      <div class="w-1/5 overflow-hidden my-3 px-3">
        <Multiselect
          v-model="value"
          :options="options"
        />

      <p>.</p>
      <p>.</p>
      <p>.</p>
      <p>.</p>
      </div>


      <div class="w-4/5 overflow-hidden border my-3 px-3">
      </div>

    </div>

  </main>
</template>

<style src="@vueform/multiselect/themes/default.css"></style>