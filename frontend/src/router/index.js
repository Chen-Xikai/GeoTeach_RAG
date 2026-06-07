import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/library',
    name: 'Library',
    component: () => import('../views/Library.vue')
  },
  {
    path: '/generator',
    name: 'Generator',
    component: () => import('../views/Generator.vue')
  },
  {
    path: '/qa',
    name: 'QA',
    component: () => import('../views/QA.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
