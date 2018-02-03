import 'babel-polyfill'
import Koa from 'koa'
import serve from 'koa-static'
import logger from 'koa-logger'
import path from 'path'
import router from './routes'

const app = new Koa()
const port = process.env.PORT || 3000
const dist = path.join(__dirname, '..', 'dist')
const errorHandler = async (ctx, next) => {
  try {
    await next();
  } catch ({ status, message }) {
    ctx.type = 'text/html'
    ctx.status = status || 500
    ctx.body = message || 'Internal Server Error'
  }
}

app
  .use(errorHandler)
  .use(logger())
  .use(router())
  .use(serve(dist))

app.listen(port, () => console.log(`[!] Server is Running on ${port}`))
