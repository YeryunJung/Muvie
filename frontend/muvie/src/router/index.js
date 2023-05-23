import Vue from "vue";
import VueRouter from "vue-router";
import HomeView from "../views/HomeView.vue";
import LoginView from "../views/LoginView.vue";
import SignupView from "../views/SignupView.vue";
import MypageView from "../views/MypageView.vue";
import MainView from "../views/MainView.vue";
import SearchView from "../views/SearchView.vue";

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView,
  },
  {
    path: "/login",
    name: "Login",
    component: LoginView,
  },
  {
    path: "/signup",
    name: "Signup",
    component: SignupView,
  },
  {
    path: "/:userId/profile",
    name: "Profile",
    component: MypageView,
  },
  {
    path: "/main",
    name: "MainView",
    component: MainView,
  },
  {
    path: "/search/:keyword",
    name: "SearchView",
    component: SearchView,
  },
];

const router = new VueRouter({
  mode: "history",
  base: process.env.BASE_URL,
  routes,
});

export default router;
