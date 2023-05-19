import Vue from "vue";
import Vuex from "vuex";
import createPersistedState from "vuex-persistedstate";
import loginStore from "./modules/loginStore";
import signupStore from "./modules/signupStore";
import mypageStore from "./modules/mypageStore";

Vue.use(Vuex);

export default new Vuex.Store({
  state: {},
  getters: {},
  mutations: {},
  actions: {},
  modules: {
    loginStore,
    signupStore,
    mypageStore,
  },
  plugins: [createPersistedState({ paths: ["loginStore"] })],
});
