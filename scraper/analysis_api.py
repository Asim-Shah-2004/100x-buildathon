import asyncio
import json
import logging
import os
import re
import traceback
from datetime import datetime

from atproto import Client, client_utils, models
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline
from dotenv import load_dotenv
load_dotenv()
class TrendAnalyzer:
    def __init__(self, logger=None):
        """
        Initialize TrendAnalyzer with logging and ML models
        """
        self.logger = logger or logging.getLogger(__name__)

        # Ensure directories exist
        self.ensure_directories_exist()

        # Initialize models
        self._init_models()

    def ensure_directories_exist(self):
        """Create necessary directories if they don't exist."""
        directories = [
            'logs',
            'data/trends',
            'analysis_results'
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def _init_models(self):
        """Initialize machine learning models"""
        try:
            # Financial sentiment model
            self.financial_sentiment = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                top_k=None
            )

            # Gemini for advanced analysis
            self.gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=os.getenv('GEMINI_KEY')  # Replace with your API key
            )
        except Exception as e:
            self.logger.error(f"Model initialization failed: {e}")
            raise

    def advanced_sentiment_analysis(self, texts):
        """Advanced sentiment analysis for given texts"""
        sentiments = []
        for text in texts:
            result = self.financial_sentiment(text)[0]
            sentiments.append({
                'text': text,
                'sentiment': result[0]['label'],
                'confidence': result[0]['score']
            })

        sentiments_sorted = sorted(sentiments, key=lambda x: x['confidence'], reverse=True)
        return {
            'top_positive': [s for s in sentiments_sorted if s['sentiment'] == 'positive'][:5],
            'top_negative': [s for s in sentiments_sorted if s['sentiment'] == 'negative'][:5],
            'total_analyzed': len(texts)
        }

    def _perform_topic_clustering(self, texts):
        """Perform topic clustering using TF-IDF and KMeans"""
        if not texts:
            return {'clusters': [], 'centroids': []}

        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        X = vectorizer.fit_transform(texts)

        n_clusters = min(3, len(texts))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(X)

        return {
            'clusters': kmeans.labels_.tolist(),
            'centroids': kmeans.cluster_centers_.tolist()
        }

    def generate_ai_insights(self, texts, category):
        """Generate AI insights using Gemini with category-specific prompts"""
        try:
            prompts = {
                'financial': PromptTemplate(
                    input_variables=['texts'],
                    template="""Analyze these financial market texts and provide:
                    1. Current market sentiment and key financial trends
                    2. Emerging investment opportunities
                    3. Potential economic risks and challenges
                    4. Sector-specific insights
                    5. Short-term and long-term market outlook
                    
                    Detailed Financial Texts: {texts}
                    
                    Analyze data (quantitative or qualitative) to identify patterns, trends, correlations, or themes. 
                    Condense the insights into concise, actionable points or narratives, highlighting key takeaways for easy understanding and decision-making.
                    Summarize in short
                    """
                ),
                'crypto': PromptTemplate(
                    input_variables=['texts'],
                    template="""Analyze these cryptocurrency and blockchain texts and provide:
                    1. Current cryptocurrency market trends
                    2. Emerging blockchain technologies
                    3. Regulatory landscape updates
                    4. Potential investment strategies
                    5. Market sentiment and volatility indicators
                    
                    Detailed Crypto Texts: {texts}
                    
                    Analyze data (quantitative or qualitative) to identify patterns, trends, correlations, or themes.
                    Condense the insights into concise, actionable points or narratives, highlighting key takeaways for easy understanding and decision-making.
                    Summarize in short
                    """
                ),
                'tech': PromptTemplate(
                    input_variables=['texts'],
                    template="""Analyze these technology industry texts and provide:
                    1. Cutting-edge technological innovations
                    2. Emerging tech trends
                    3. Potential disruptive technologies
                    4. Industry investment opportunities
                    5. Impact of recent technological developments
                    
                    Detailed Tech Texts: {texts}
                    
                    Analyze data (quantitative or qualitative) to identify patterns, trends, correlations, or themes.
                    Condense the insights into concise, actionable points or narratives, highlighting key takeaways for easy understanding and decision-making.
                    Summarize in short
                    """
                ),
                'entertainment': PromptTemplate(
                    input_variables=['texts'],
                    template="""Analyze these entertainment industry texts and provide:
                    1. Current entertainment trends
                    2. Emerging content and media innovations
                    3. Audience engagement insights
                    4. Potential industry shifts
                    5. Notable upcoming releases and developments
                    
                    Detailed Entertainment Texts: {texts}
                    
                    Analyze data (quantitative or qualitative) to identify patterns, trends, correlations, or themes.
                    Condense the insights into concise, actionable points or narratives, highlighting key takeaways for easy understanding and decision-making.
                    Summarize in short
                    """
                )
            }

            # Select the appropriate prompt based on category
            # Modified to handle variations in input and provide a fallback
            normalized_category = category.lower().strip()

            # Mapping to handle potential variations
            category_map = {
                'finance': 'financial',
                'crypto': 'crypto',
                'cryptocurrency': 'crypto',
                'tech': 'tech',
                'technology': 'tech',
                'entertainment': 'entertainment',
                'media': 'entertainment'
            }

            # Get the standardized category or fallback to a default
            standard_category = category_map.get(normalized_category, 'tech')

            # Select prompt, with tech as the ultimate fallback
            prompt = prompts.get(standard_category, prompts['tech'])

            chain = LLMChain(llm=self.gemini_llm, prompt=prompt)
            result = chain.run(
                texts='\n'.join(texts[:10]),
                category=standard_category
            )
            return str(result)
        except Exception as e:
            self.logger.error(f"AI insights generation error for {category}: {e}")
            return f"Trending insights for {category}: Key developments observed"

    def analyze_trend_data(self, category):
        """Analyze trend data for a specific category"""
        try:
            # Load trend data
            filepath = os.path.join('data', 'trends', f'{category}_trends.json')

            with open(filepath, 'r', encoding='utf-8') as f:
                trend_data = json.load(f)

            # Extract texts from top posts
            texts = [post['text'] for post in trend_data['post_metrics']['top_posts']]

            if not texts:
                self.logger.warning(f"No texts found for {category} trends")
                return None

            # Perform analyses
            sentiments = self.advanced_sentiment_analysis(texts)
            topics = self._perform_topic_clustering(texts)

            # Generate AI insights (synchronous for now)
            ai_insights = self.generate_ai_insights(texts, category)

            # Prepare trend analysis
            trend_analysis = {
                'category': category,
                'topHashtags': trend_data.get('top_hashtags', []),
                'post_metrics': trend_data.get('post_metrics', {}),
                'sentiment_analysis': sentiments,
                'topic_clusters': topics,
                'ai_insights': ai_insights
            }

            # Save analysis result
            output_file = os.path.join('analysis_results', f'{category}_trend_analysis.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(trend_analysis, f, indent=2)

            self.logger.info(f"Analysis completed for {category}")
            return trend_analysis

        except Exception as e:
            self.logger.error(f"Error in {category} trend analysis: {e}")
            traceback.print_exc()
            return None


class BlueskyPoster:
    def __init__(self, logger=None):
        """Initialize Bluesky Poster"""
        self.logger = logger or logging.getLogger(__name__)
        self.client = Client()

        # Initialize Gemini for post generation
        self.gemini_llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=os.getenv('GEMINI_KEY')  # Replace with your API key
        )

    def format_post(self, text, max_length=300):
        """Format post for Bluesky"""
        text = ' '.join(text.split())
        if len(text) > max_length:
            sentences = text.split('. ')
            truncated_text = ''
            for sentence in sentences:
                if len(truncated_text) + len(sentence) + 3 <= max_length:
                    truncated_text += sentence + '. '
                else:
                    break
            text = (truncated_text.strip() + '...').strip()[:max_length]
        return text

    def split_content_into_chunks(self, content: str, max_length: int = 299):
        """Split content into chunks that fit Bluesky's character limit"""
        # Use regex to split sentences more robustly
        import re
        sentences = re.split(r'(?<=[.!?])\s+', content)
        chunks = []
        current_chunk = ''

        for sentence in sentences:
            if len(current_chunk + sentence) <= max_length:
                current_chunk += sentence + ' '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence[:max_length]

        if current_chunk:
            chunks.append(current_chunk.strip())

        return list(chunks)

    def generate_post(self, analysis_file):
        """Generate Bluesky post from trend analysis"""
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)

            category = analysis_data['category']
            insights = str(analysis_data.get('ai_insights', ''))

            # Clean up hashtags
            top_hashtags = analysis_data.get('topHashtags', [])

            # Ensure hashtags are clean strings
            safe_hashtags = []
            for tag in top_hashtags:
                # If tag is a dictionary, extract the hashtag name
                if isinstance(tag, dict):
                    hashtag_name = tag.get('hashtag', '')
                    # Only add if it's a non-empty string
                    if hashtag_name:
                        safe_hashtags.append(f'#{hashtag_name}')
                # If tag is already a string, just ensure it starts with #
                elif isinstance(tag, str):
                    safe_hashtags.append(f'#{tag}' if not tag.startswith('#') else tag)

            # Limit to 2 hashtags
            safe_hashtags = safe_hashtags[:2]

            # Fallback hashtags if no safe hashtags found
            default_hashtags = {
                'financial': ['#Finance', '#Investment'],
                'tech': ['#TechTrends', '#Innovation'],
                'crypto': ['#Crypto', '#Blockchain'],
                'entertainment': ['#EntertainmentNews', '#PopCulture']
            }

            # Use safe hashtags or default hashtags
            hashtags = safe_hashtags if safe_hashtags else default_hashtags.get(category, ['#Trends'])
            hashtag_string = ' '.join(hashtags)

            # Rest of the method remains the same...

            # Robust prompt template
            prompts = {
                'financial': f"📈 Financial Pulse: Market insights and investment snapshot. {hashtag_string}",
                'tech': f"🚀 Tech Frontier: Innovation highlights and emerging trends. {hashtag_string}",
                'crypto': f"🪙 Crypto Momentum: Blockchain updates and market pulse. {hashtag_string}",
                'entertainment': f"🎬 Entertainment Buzz: Pop culture and trending entertainment. {hashtag_string}"
            }

            # Fallback to a generic prompt if category not found
            prompt = prompts.get(category, prompts['financial'])

            # Use Gemini to refine and format the post
            prompt_template = PromptTemplate(
                input_variables=['insights', 'prompt'],
                template="""Refine this post to be engaging, informative, and within 500 characters:

    Original Prompt: {prompt}

    Additional Context: {insights}

    Guideline:
    - Keep it under 500 characters.
    - Capture key insights.
    - Use an engaging tone.
    - Maintain core message.
    - Avoid complex dictionary or list representations.
    - Use Hashtags aggressively within message for engaging with more audience.
    - Use emojis aggressively for engaging with more audience.
    - Do not use points.
    """
            )

            chain = LLMChain(llm=self.gemini_llm, prompt=prompt_template)
            post_text = chain.run({
                'insights': insights,
                'prompt': prompt
            })

            # Ensure post is not empty and fits character limit
            # formatted_post = self.format_post(str(post_text))
            #
            # # Additional fallback for empty posts
            # if not formatted_post or len(formatted_post) < 10:
            #     fallback_posts = {
            #         'financial': f"📈 Market pulse: Strategic insights for smart investors! {hashtag_string}",
            #         'tech': f"🚀 Tech world: Innovations shaping our digital future! {hashtag_string}",
            #         'crypto': f"₿ Crypto insights: Blockchain breaking new ground! {hashtag_string}",
            #         'entertainment': f"🎬 Entertainment spotlight: Creativity meets excitement! {hashtag_string}"
            #     }
            #     formatted_post = fallback_posts.get(category, fallback_posts['tech'])

            return self.split_content_into_chunks(post_text)

        except Exception as e:
            self.logger.error(f"Post generation error: {e}")
            traceback.print_exc()
            return None

    def post_to_bluesky(self, post):
        """Post to Bluesky"""
        if not post:
            return False

        try:

            self.client.login(os.getenv('BLUESKY_HANDLE_'), os.getenv('BLUESKY_PASSWORD_'))
            previous_post_ref = None
            root_post = None
            parent_post = None
            for post_text in post:
                post_text = post_text.replace("*", "")
                if root_post is None:
                    root_post = models.create_strong_ref(self.client.send_post(
                        text=parse_text_to_facets(post_text),
                    ))
                    parent_post = root_post
                else:
                    parent_post = models.create_strong_ref(self.client.send_post(
                        text=parse_text_to_facets(post_text),
                        reply_to=models.AppBskyFeedPost.ReplyRef(parent=parent_post, root=root_post)
                    ))
                self.logger.info(f"Posted: {post_text}")
            # self.client.send_post(text=parse_text_to_facets(post))
            return True
        except Exception as e:
            self.logger.error(f"Bluesky posting failed: {e}")
            traceback.print_exc()
            return False


def setup_logging():
    """Set up logging configuration"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'trend_poster_{timestamp}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


async def main():
    """Main workflow"""
    logger = setup_logging()
    logger.info("Trend Analysis and Bluesky Poster Starting...")

    # Initialize components
    trend_analyzer = TrendAnalyzer(logger)
    bluesky_poster = BlueskyPoster(logger)

    # Categories to process
    categories = ['finance', 'crypto', 'entertainment', 'tech']

    try:
        # Analyze trends for each category
        for category in categories:
            # Analyze trend and save results
            trend_analysis = trend_analyzer.analyze_trend_data(category)

            if trend_analysis:
                # Generate Bluesky post from analysis
                analysis_file = os.path.join('analysis_results', f'{category}_trend_analysis.json')
                post = bluesky_poster.generate_post(analysis_file)

                # Post to Bluesky
                if post:
                    bluesky_poster.post_to_bluesky(post)

                # Add a small delay between posts
                await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Workflow error: {e}")
        traceback.print_exc()


def parse_text_to_facets(text):
    """
    Parse a string and automatically create appropriate facets for mentions, links, and tags.

    Args:
        text (str): Input text to parse and create facets for

    Returns:
        client_utils.TextBuilder: TextBuilder object with detected facets
    """
    # Initialize TextBuilder
    text_builder = client_utils.TextBuilder()

    # Regular expressions for detection
    mention_pattern = r'@(\w+)'
    url_pattern = r'https?://\S+'
    tag_pattern = r'#(\w+)'

    # Keep track of last processed index to handle overlapping matches
    last_index = 0

    # Find all matches
    all_matches = []

    # Collect mentions
    for match in re.finditer(mention_pattern, text):
        all_matches.append(('mention', match))

    # Collect URLs
    for match in re.finditer(url_pattern, text):
        all_matches.append(('link', match))

    # Collect tags
    for match in re.finditer(tag_pattern, text):
        all_matches.append(('tag', match))

    # Sort matches by their start index
    all_matches.sort(key=lambda x: x[1].start())

    # Process matches
    for match_type, match in all_matches:
        # Add text before the match
        if match.start() > last_index:
            text_builder.text(text[last_index:match.start()])

        # Add the matched content with appropriate facet
        if match_type == 'mention':
            # Assumes a did lookup or placeholder - in real world, you'd want to resolve the DID
            text_builder.mention(match.group(1), f'did:placeholder:{match.group(1)}')
        elif match_type == 'link':
            text_builder.link(match.group(0), match.group(0))
        elif match_type == 'tag':
            text_builder.tag(f'#{match.group(1)}', match.group(1))

        # Update last processed index
        last_index = match.end()

    # Add any remaining text
    if last_index < len(text):
        text_builder.text(text[last_index:])

    return text_builder


async def run_workflow_periodically():
    """Run the main workflow periodically every 10 minutes"""
    logger = setup_logging()
    logger.info("Starting periodic Trend Analysis and Bluesky Poster...")

    while True:
        try:
            # Initialize components
            trend_analyzer = TrendAnalyzer(logger)
            bluesky_poster = BlueskyPoster(logger)

            # Categories to process
            categories = ['finance', 'crypto', 'entertainment', 'tech']

            # Analyze trends for each category
            for category in categories:
                # Analyze trend and save results
                trend_analysis = trend_analyzer.analyze_trend_data(category)

                if trend_analysis:
                    # Generate Bluesky post from analysis
                    analysis_file = os.path.join('analysis_results', f'{category}_trend_analysis.json')
                    post = bluesky_poster.generate_post(analysis_file)

                    # Post to Bluesky
                    if post:
                        bluesky_poster.post_to_bluesky(post)

                    # Add a small delay between posts
                    await asyncio.sleep(2)

            # Log the completion of a workflow cycle
            logger.info("Workflow cycle completed. Waiting for next cycle...")

            # Wait for 10 minutes before next run
            await asyncio.sleep(30 * 60)  # 600 seconds = 10 minutes

        except Exception as e:
            logger.error(f"Periodic workflow error: {e}")
            traceback.print_exc()

            # Wait 10 minutes even if an error occurs
            await asyncio.sleep(900)


async def main():
    """Main entry point with periodic workflow"""
    # Create a task for the periodic workflow
    workflow_task = asyncio.create_task(run_workflow_periodically())

    # Wait indefinitely to keep the script running
    await workflow_task


if __name__ == '__main__':
    asyncio.run(main())
