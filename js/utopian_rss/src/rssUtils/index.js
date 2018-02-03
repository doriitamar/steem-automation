import steem from 'steem'
import RSS from 'rss'
import xml from 'xml'
import { promisify } from 'util'
import { FEED_URL } from '../config'

const getDiscussionsByCreated = promisify(steem.api.getDiscussionsByCreated);
const getDiscussionsByFeed = promisify(steem.api.getDiscussionsByFeed);
const getDiscussionsByBlog = promisify(steem.api.getDiscussionsByBlog);
const getDiscussionsByHot = promisify(steem.api.getDiscussionsByHot);
const getDiscussionsByTrending = promisify(steem.api.getDiscussionsByTrending);

const rssGenerator = async (category, tag) => {
    const feedOption = {
        title: 'UtopianRSS',
        feed_url: `https://${FEED_URL}/${tag}`,
        site_url: `https://steemit.com/created/${tag}`,
        image_url: 'https://steemit.com/images/steemit-share.png',
        docs: 'https://github.com/utopian-io/steem-automation/'
    } 

        const apiResponse = await getContent(category, tag)
        const feed = new RSS(feedOption)
        const completedFeed = await feedItem(feed, apiResponse)
        return completedFeed.xml()
}

const methodMap = {
    'feed': (query) => getDiscussionsByFeed(query),
    'blog': (query) => getDiscussionsByBlog(query),
    'new': (query) => getDiscussionsByCreated(query),
    'hot': (query) => getDiscussionsByHot(query),
    'trend': (query) => getDiscussionsByTrending(query)
}

const getContent = async (category, tag) => methodMap.hasOwnProperty(category) ?
                                            await methodMap[category]({tag, limit: 10}) :
                                            Promise.reject({status: 400, message: "Unknown Category"})


const feedItem = async (feed, response) => {
    response.forEach(({title, url, author, category, created: date}) => {
        feed.item({
            title,
            url: `https://steemit.com${url}`,
            categories: [category],
            author,
            date
        })
    });

    return feed
}

export default rssGenerator;