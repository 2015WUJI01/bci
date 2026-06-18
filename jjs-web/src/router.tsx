import {
  createRootRoute,
  createRoute,
  createRouter,
  redirect,
} from '@tanstack/react-router'
import { useAuthStore } from '@/stores/authStore'
import { AuthPage } from '@/pages/AuthPage'
import { GameLayout } from '@/pages/GameLayout'
import { MarketPage } from '@/pages/MarketPage'
import { PortfolioPage } from '@/pages/PortfolioPage'
import { TradePage } from '@/pages/TradePage'
import { CompanyPage } from '@/pages/CompanyPage'
import { QuarterlyPage } from '@/pages/QuarterlyPage'
import { LeaderboardPage } from '@/pages/LeaderboardPage'

const rootRoute = createRootRoute()

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: () => {
    if (useAuthStore.getState().isAuthenticated) {
      throw redirect({ to: '/game/market' })
    }
    throw redirect({ to: '/login' })
  },
  component: () => null,
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: AuthPage,
})

const gameRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/game',
  beforeLoad: () => {
    if (!useAuthStore.getState().isAuthenticated) {
      throw redirect({ to: '/login' })
    }
  },
  component: GameLayout,
})

const marketRoute = createRoute({
  getParentRoute: () => gameRoute,
  path: '/market',
  component: MarketPage,
})

const portfolioRoute = createRoute({
  getParentRoute: () => gameRoute,
  path: '/portfolio',
  component: PortfolioPage,
})

const tradeRoute = createRoute({
  getParentRoute: () => gameRoute,
  path: '/trade',
  component: TradePage,
})

const companyRoute = createRoute({
  getParentRoute: () => gameRoute,
  path: '/company',
  component: CompanyPage,
})

const quarterlyRoute = createRoute({
  getParentRoute: () => gameRoute,
  path: '/company/quarterly',
  component: QuarterlyPage,
})

const leaderboardRoute = createRoute({
  getParentRoute: () => gameRoute,
  path: '/leaderboard',
  component: LeaderboardPage,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  gameRoute.addChildren([
    marketRoute,
    portfolioRoute,
    tradeRoute,
    companyRoute,
    quarterlyRoute,
    leaderboardRoute,
  ]),
])

export const router = createRouter({ routeTree })
