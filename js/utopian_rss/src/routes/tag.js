import Router from 'koa-router'
import rssGenerator from '../rssUtils'

const router = new Router({ prefix: '' })

router.get('/:category/:tag', async (ctx, next) => {
    ctx.type = 'text/xml'
    ctx.body = await rssGenerator(ctx.params.category, ctx.params.tag)   
})

export default router
