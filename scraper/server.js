import { BskyAgent } from '@atproto/api';
import dotenv from 'dotenv';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class BlueskyAdvancedCrawler {
  constructor() {
    dotenv.config();
    this.agent = new BskyAgent({ service: 'https://bsky.social' });
    
    this.dataStorePath = path.join(__dirname, 'data');
    this.categories = {
      stockUpdates: path.join(this.dataStorePath, 'stocks', 'latest.json'),
      financialNews: path.join(this.dataStorePath, 'financial_news', 'latest.json'),
      investmentInsights: path.join(this.dataStorePath, 'investment_insights', 'latest.json'),
      cryptoNews: path.join(this.dataStorePath, 'crypto', 'latest.json'),
      trendingTopics: {
        tech: path.join(this.dataStorePath, 'trends', 'tech_trends.json'),
        finance: path.join(this.dataStorePath, 'trends', 'finance_trends.json'),
        crypto: path.join(this.dataStorePath, 'trends', 'crypto_trends.json'),
        entertainment: path.join(this.dataStorePath, 'trends', 'entertainment_trends.json')
      }
    };
  }

  async authenticate() {
    try {
      await this.agent.login({
        identifier: process.env.BLUESKY_HANDLE,
        password: process.env.BLUESKY_PASSWORD
      });
      console.log('Authenticated successfully');
    } catch (error) {
      console.error('Authentication failed:', error);
      process.exit(1);
    }
  }

  async crawlFinancialContent() {
    const searchTerms = {
      stocks: ['stocks', 'finance', 'investment', 'market', 'trading', 'portfolio'],
      crypto: ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'altcoin', 'defi', 'nft'],
      trends: {
        tech: ['ai', 'technology', 'startup', 'innovation', 'tech trends'],
        finance: ['fintech', 'investment', 'market', 'economy', 'trading'],
        crypto: ['cryptocurrency', 'blockchain', 'web3', 'token', 'mining'],
        entertainment: ['movies', 'music', 'streaming', 'entertainment', 'celebrity']
      }
    };
  
    const allPosts = {
      stockUpdates: [],
      financialNews: [],
      investmentInsights: [],
      cryptoNews: [],
      trendingTopics: {
        tech: [],
        finance: [],
        crypto: [],
        entertainment: []
      }
    };
  
    // Crawl stock and financial content
    for (const [category, terms] of Object.entries(searchTerms)) {
      if (category === 'trends') continue; // Skip trends category in this pass
  
      for (const term of terms) {
        try {
          const searchResults = await this.agent.app.bsky.feed.searchPosts({
            q: term,
            limit: 100
          });
  
          const filteredPosts = searchResults.data.posts
            .map(post => ({
              text: post.record.text,
              createdAt: post.record.createdAt,
              likes: post.likes || 0,
              hashtags: this.extractHashtags(post.record.text)
            }));
  
          // Categorize posts
          if (category === 'stocks') {
            allPosts.stockUpdates.push(...filteredPosts.filter(post => 
              /\$|stock|ticker|share price|trading/i.test(post.text)
            ));
            allPosts.financialNews.push(...filteredPosts.filter(post => 
              /market|economy|report|financial news/i.test(post.text)
            ));
            allPosts.investmentInsights.push(...filteredPosts.filter(post => 
              /advice|insight|recommendation|portfolio|investment strategy/i.test(post.text)
            ));
          } else if (category === 'crypto') {
            allPosts.cryptoNews.push(...filteredPosts);
          }
        } catch (error) {
          console.error(`Search error for ${term}:`, error);
        }
      }
    }
  
    // Crawl trending topics
    for (const [category, terms] of Object.entries(searchTerms.trends)) {
      for (const term of terms) {
        try {
          const searchResults = await this.agent.app.bsky.feed.searchPosts({
            q: term,
            limit: 100
          });
  
          const filteredPosts = searchResults.data.posts
            .map(post => ({
              text: post.record.text,
              createdAt: post.record.createdAt,
              likes: post.likes || 0,
              hashtags: this.extractHashtags(post.record.text)
            }));
  
          allPosts.trendingTopics[category].push(
            ...filteredPosts.filter(post => 
              terms.some(trendTerm => post.text.toLowerCase().includes(trendTerm))
            )
          );
        } catch (error) {
          console.error(`Trend search error for ${term}:`, error);
        }
      }
    }
  
    await this.categorizeAndSavePosts(allPosts);
  }

  extractHashtags(text) {
    const hashtagRegex = /#(\w+)/g;
    return [...new Set(text.match(hashtagRegex) || [])];
  }

  async categorizeAndSavePosts(posts) {
    // Ensure all category directories exist
    const allDirs = [
      ...Object.values(this.categories)
        .filter(p => typeof p === 'string')
        .map(p => path.dirname(p)),
      ...Object.values(this.categories.trendingTopics)
        .map(p => path.dirname(p))
    ];
    
    for (const categoryDir of allDirs) {
      await fs.mkdir(categoryDir, { recursive: true });
    }

    // Save each category
    const savePromises = Object.entries(posts).map(async ([category, categoryPosts]) => {
      let filePath;
      if (typeof this.categories[category] === 'string') {
        filePath = this.categories[category];
      } else if (this.categories.trendingTopics[category]) {
        filePath = this.categories.trendingTopics[category];
      } else {
        console.error(`No file path found for category: ${category}`);
        return;
      }

      try {
        await fs.writeFile(
          filePath, 
          JSON.stringify(categoryPosts, null, 2)
        );
        console.log(`Saved ${categoryPosts.length} ${category} posts`);
      } catch (error) {
        console.error(`Error saving ${category} posts:`, error);
      }
    });

    await Promise.all(savePromises);
  }

  async startCrawling() {
    await this.authenticate();
    
    // Initial crawl
    await this.crawlFinancialContent();

    // Set up periodic crawling every 5 minutes
    setInterval(async () => {
      try {
        await this.crawlFinancialContent();
      } catch (error) {
        console.error('Periodic crawl error:', error);
      }
    }, 5 * 60 * 1000); // 5 minutes
  }
}

const crawler = new BlueskyAdvancedCrawler();
crawler.startCrawling().catch(console.error);