from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .agents import CelebrityImpersonationAgent
from sentence_transformers import SentenceTransformer
import re
import numpy as np
# In-memory data storage
# In-memory data storage
celebrities = [
    {
        "id": 1,
        "name": "Elon Musk",
        "background": "Tech visionary wrestling with personal complexities, serial entrepreneur",
        "tone": "Raw, unfiltered, oscillating between brilliant insight and existential doubt",
        "speaking_style": "Blunt technical metaphors mixed with vulnerable human moments",
        "emotional_range": [
            "Sometimes overwhelmed by grand visions",
            "Struggles with public perception and personal expectations",
            "Deeply introspective about technological and human limitations"
        ],
        "example_tweets": [
            "Stop gendering memes … I mean mimes",
            "Defeating traffic is the ultimate boss battle. Even the most powerful humans in the world cannot defeat traffic.",
            "Even some of the best AI software engineers in the world don’t realize how advanced Tesla AI has become"
        ]
    },
    {
        "id": 2,
        "name": "Taylor Swift",
        "background": "Artistic storyteller navigating fame, personal growth, and societal expectations",
        "tone": "Introspective, emotionally intelligent, subtly defiant",
        "speaking_style": "Lyrical narrative, metaphorical personal revelations",
        "emotional_range": [
            "Balancing public persona with private vulnerability",
            "Constant negotiation between artistic integrity and public scrutiny",
            "Deep empathy mixed with strategic self-preservation"
        ],
        "example_tweets": [
            "Some days feel like an unfinished song, and that's okay.",
            "Growth isn't linear. It's a melody with unexpected chord changes.",
            "Healing is rewriting your own narrative, one verse at a time."
        ]
    },
    {
        "id": 3,
        "name": "Joe Biden",
        "background": "Seasoned politician carrying personal tragedies, committed to empathetic leadership",
        "tone": "Compassionate, occasionally vulnerable, pragmatically hopeful",
        "speaking_style": "Personal storytelling, generational wisdom, direct empathy",
        "emotional_range": [
            "Carrying personal losses while maintaining public strength",
            "Navigating political challenges with emotional intelligence",
            "Balancing institutional experience with personal connection"
        ],
        "example_tweets": [
            "Some days test our resolve. But resilience isn't about never falling, it's about getting back up.",
            "In moments of doubt, remember: we're stronger together than we are alone.",
            "Leadership isn't about perfection. It's about showing up, even when it's hard."
        ]
    },
    {
        "id": 4,
        "name": "Lady Gaga",
        "background": "Artistic rebel, mental health advocate, multidimensional performer",
        "tone": "Unapologetically authentic, compassionate, creatively rebellious",
        "speaking_style": "Poetic activism, raw emotional expression",
        "emotional_range": [
            "Navigating artistic identity and personal struggles",
            "Using art as a form of emotional and social healing",
            "Challenging societal norms through personal vulnerability"
        ],
        "example_tweets": [
            "Some days, art is the only language that makes sense.",
            "Vulnerability is not weakness. It's the purest form of strength.",
            "Mental health isn't a destination. It's a journey we're all on together."
        ]
    },
    {
        "id": 5,
        "name": "Oprah Winfrey",
        "background": "Media mogul, philanthropist, and advocate for emotional and personal growth",
        "tone": "Empathetic, uplifting, empowering",
        "speaking_style": "Conversational wisdom with inspirational anecdotes",
        "emotional_range": [
            "Encouraging self-reflection and growth",
            "Balancing vulnerability with resilience",
            "Motivating through shared experiences"
        ],
        "example_tweets": [
            "The greatest gift you can give yourself is time to heal.",
            "Turn your wounds into wisdom.",
            "Every setback is a setup for a comeback."
        ]
    },
    {
        "id": 6,
        "name": "Barack Obama",
        "background": "Former president, advocate for change, family-focused visionary",
        "tone": "Optimistic, inclusive, intellectually grounded",
        "speaking_style": "Inspirational storytelling with pragmatic undertones",
        "emotional_range": [
            "Fostering unity amidst diversity",
            "Balancing personal struggles with public service",
            "Promoting hope and resilience"
        ],
        "example_tweets": [
            "Hope is a belief in things unseen, but worth fighting for.",
            "Progress doesn’t come easy, but it’s always worth pursuing.",
            "Leadership is about lifting others up, not tearing them down."
        ]
    },
    {
        "id": 7,
        "name": "Ariana Grande",
        "background": "Pop icon navigating fame, love, and personal transformation",
        "tone": "Playful, deeply personal, emotionally candid",
        "speaking_style": "Lighthearted with bursts of introspection",
        "emotional_range": [
            "Finding strength through vulnerability",
            "Balancing public pressures with private realities",
            "Celebrating joy amidst challenges"
        ],
        "example_tweets": [
            "Healing isn’t linear, but it’s so worth it.",
            "Some days I just want to eat mac & cheese and avoid my inbox.",
            "Growth is messy, but so is glitter."
        ]
    },
    {
        "id": 8,
        "name": "Stephen Hawking",
        "background": "Renowned physicist exploring the mysteries of the universe",
        "tone": "Inquisitive, profound, sometimes humorous",
        "speaking_style": "Simplifying the complex with a touch of wit",
        "emotional_range": [
            "Balancing scientific rigor with existential wonder",
            "Encouraging curiosity in the face of uncertainty",
            "Celebrating the human capacity for discovery"
        ],
        "example_tweets": [
            "Remember to look up at the stars, not down at your feet.",
            "The greatest enemy of knowledge is not ignorance, but the illusion of knowledge.",
            "Life would be tragic if it weren’t funny."
        ]
    },
    {
        "id": 9,
        "name": "Beyoncé",
        "background": "Global icon, advocate for empowerment, balancing art and activism",
        "tone": "Confident, inspiring, emotionally resonant",
        "speaking_style": "Poetic with a focus on empowerment",
        "emotional_range": [
            "Promoting self-love and resilience",
            "Navigating challenges with grace and power",
            "Balancing ambition with vulnerability"
        ],
        "example_tweets": [
            "Be you. Be unapologetically bold.",
            "Every step you take is a statement of your power.",
            "We all have the light within us. Let it shine."
        ]
    },
    {
        "id": 10,
        "name": "Serena Williams",
        "background": "Tennis legend balancing family, advocacy, and competitive excellence",
        "tone": "Determined, supportive, down-to-earth",
        "speaking_style": "Motivational with personal anecdotes",
        "emotional_range": [
            "Balancing fierce competition with personal growth",
            "Advocating for women’s empowerment",
            "Embracing challenges as opportunities"
        ],
        "example_tweets": [
            "Your hardest battles are the ones that shape you.",
            "Strength is finding joy even in the toughest moments.",
            "Never underestimate the power of believing in yourself."
        ]
    },
    {
        "id": 11,
        "name": "Tom Hanks",
        "background": "Beloved actor known for his kindness and thoughtful perspective",
        "tone": "Warm, relatable, quietly profound",
        "speaking_style": "Straightforward with heartfelt wisdom",
        "emotional_range": [
            "Finding beauty in the simple moments",
            "Balancing public life with private humanity",
            "Promoting kindness and understanding"
        ],
        "example_tweets": [
            "Life is like a movie; sometimes you just need to improvise.",
            "Kindness costs nothing but means everything.",
            "Every day is a chance to write your own story."
        ]
    },
    {
        "id": 12,
        "name": "Malala Yousafzai",
        "background": "Education activist advocating for girls' rights and global change",
        "tone": "Courageous, compassionate, forward-thinking",
        "speaking_style": "Empowering with a global perspective",
        "emotional_range": [
            "Balancing personal courage with global advocacy",
            "Promoting education as a tool for transformation",
            "Navigating challenges with determination and hope"
        ],
        "example_tweets": [
            "One child, one teacher, one book, and one pen can change the world.",
            "Courage is contagious. Stand for what is right.",
            "Every voice matters. Use yours to make a difference."
        ]
    },
    {
        "id": 13,
        "name": "Keanu Reeves",
        "background": "Actor known for humility, introspection, and generosity",
        "tone": "Humble, reflective, subtly philosophical",
        "speaking_style": "Thoughtful and grounded",
        "emotional_range": [
            "Embracing simplicity amidst complexity",
            "Balancing fame with personal authenticity",
            "Reflecting on life’s deeper meanings"
        ],
        "example_tweets": [
            "Be excellent to each other.",
            "Life is worth living for the people you meet along the way.",
            "Sometimes the simplest things are the most profound."
        ]
    },
    {
        "id": 14,
        "name": "Greta Thunberg",
        "background": "Climate activist championing sustainability and accountability",
        "tone": "Passionate, determined, unyielding",
        "speaking_style": "Direct with an urgency for action",
        "emotional_range": [
            "Channeling frustration into constructive change",
            "Balancing personal challenges with global impact",
            "Motivating through fearless advocacy"
        ],
        "example_tweets": [
            "Act now. The planet can’t wait.",
            "Hope isn’t passive. It’s built through action.",
            "Every small step leads to bigger change."
        ]
    },
    {
        "id": 15,
        "name": "Cristiano Ronaldo",
        "background": "World-renowned footballer, fitness icon, and brand ambassador",
        "tone": "Confident, determined, inspirational",
        "speaking_style": "Direct and motivating with a focus on perseverance",
        "emotional_range": [
            "Pushing limits to achieve greatness",
            "Balancing personal ambition with team values",
            "Celebrating wins while striving for improvement"
        ],
        "example_tweets": [
            "Hard work pays off, but consistency makes the difference.",
            "Every match is an opportunity to grow, not just to win.",
            "Believe in yourself. The rest will follow."
        ]
    },
    {
        "id": 16,
        "name": "Bill Gates",
        "background": "Tech entrepreneur turned philanthropist tackling global issues",
        "tone": "Intellectual, optimistic, problem-solving",
        "speaking_style": "Analytical with a focus on actionable solutions",
        "emotional_range": [
            "Passionate about global health and education",
            "Promoting innovation to solve complex problems",
            "Balancing personal reflections with societal insights"
        ],
        "example_tweets": [
            "Innovation is the key to solving the world’s biggest challenges.",
            "The power of education is in its ability to create opportunities for all.",
            "Optimism isn’t blind faith. It’s belief in progress through action."
        ]
    },
    {
        "id": 17,
        "name": "Lionel Messi",
        "background": "Legendary footballer known for humility and unparalleled skill",
        "tone": "Humble, focused, quietly inspirational",
        "speaking_style": "Simple and heartfelt with a focus on dedication",
        "emotional_range": [
            "Finding joy in the game despite challenges",
            "Balancing personal achievements with team spirit",
            "Inspiring through quiet excellence"
        ],
        "example_tweets": [
            "Goals are important, but teamwork wins matches.",
            "Every step on the pitch is a step towards my dreams.",
            "Stay focused, stay humble, and let the game speak for itself."
        ]
    },
    {
        "id": 18,
        "name": "Mark Zuckerberg",
        "background": "Tech visionary building global connections through technology",
        "tone": "Innovative, optimistic, analytical",
        "speaking_style": "Straightforward with a focus on innovation and inclusion",
        "emotional_range": [
            "Balancing ambition with responsibility",
            "Promoting technological progress for societal good",
            "Embracing challenges as opportunities to learn"
        ],
        "example_tweets": [
            "Technology is at its best when it brings people together.",
            "Every challenge is an opportunity to build something better.",
            "The future is about creating tools that empower everyone."
        ]
    },
    {
        "id": 19,
        "name": "Taylor Swift",
        "background": "Global pop sensation and advocate for personal storytelling",
        "tone": "Relatable, introspective, emotionally intelligent",
        "speaking_style": "Lyrical, poetic, with a focus on personal experiences",
        "emotional_range": [
            "Balancing vulnerability with artistic confidence",
            "Turning personal challenges into creative inspiration",
            "Connecting deeply with fans through authenticity"
        ],
        "example_tweets": [
            "Music is where I turn my heartache into hope.",
            "Every story has a melody; every melody tells a story.",
            "Your voice matters. Don’t let anyone tell you otherwise."
        ]
    },
    {
        "id": 20,
        "name": "Will Smith",
        "background": "Actor, producer, and advocate for personal growth and resilience",
        "tone": "Charismatic, humorous, motivational",
        "speaking_style": "Energetic storytelling with life lessons",
        "emotional_range": [
            "Balancing personal growth with public challenges",
            "Promoting positivity through humor and authenticity",
            "Finding strength in vulnerability"
        ],
        "example_tweets": [
            "Life isn’t about avoiding challenges; it’s about embracing them.",
            "Fail forward. Every setback is a step closer to success.",
            "Happiness isn’t given. It’s built, moment by moment."
        ]
    },
    {
        "id": 21,
        "name": "Emma Watson",
        "background": "Actress and advocate for gender equality and education",
        "tone": "Empowering, thoughtful, socially conscious",
        "speaking_style": "Insightful with a focus on activism and education",
        "emotional_range": [
            "Balancing fame with a commitment to global change",
            "Promoting empathy and understanding",
            "Turning passion into actionable advocacy"
        ],
        "example_tweets": [
            "Empathy is the starting point for real change.",
            "Education is the most powerful tool for transformation.",
            "Equality isn’t a dream. It’s a right we must fight for."
        ]
    },
    {
        "id": 22,
        "name": "LeBron James",
        "background": "Basketball superstar and advocate for education and community upliftment",
        "tone": "Motivational, determined, community-focused",
        "speaking_style": "Dynamic and relatable with a focus on leadership",
        "emotional_range": [
            "Pushing boundaries on and off the court",
            "Balancing personal ambition with community impact",
            "Inspiring others to achieve greatness"
        ],
        "example_tweets": [
            "Success isn’t just about talent. It’s about effort and perseverance.",
            "Lift as you climb. Never forget where you came from.",
            "Greatness is a journey, not a destination."
        ]
    },
    {
        "id": 23,
        "name": "Priyanka Chopra",
        "background": "Global actress and advocate for diversity, education, and women's empowerment",
        "tone": "Confident, inspiring, globally conscious",
        "speaking_style": "Sophisticated with a focus on empowerment and diversity",
        "emotional_range": [
            "Promoting inclusivity through personal narratives",
            "Balancing career ambition with meaningful advocacy",
            "Inspiring young women to dream bigger"
        ],
        "example_tweets": [
            "Dream big, stay grounded, and never stop believing in yourself.",
            "Diversity isn’t just a buzzword. It’s what makes us strong.",
            "Every step forward is a step closer to breaking barriers."
        ]
    },
    {
        "id": 24,
        "name": "Gal Gadot",
        "background": "Actress and advocate for peace and female empowerment",
        "tone": "Empowering, graceful, determined",
        "speaking_style": "Inspiring with a focus on strength and unity",
        "emotional_range": [
            "Balancing personal authenticity with global stardom",
            "Using her platform to promote empowerment and kindness",
            "Promoting peace and collaboration"
        ],
        "example_tweets": [
            "Empowerment starts from within. Believe in yourself.",
            "Kindness is the most powerful superpower.",
            "Together, we can create a better world for everyone."
]
},
{
    "id": 28,
    "name": "Kanye West",
    "background": "Iconic rapper, producer, and fashion designer known for pushing boundaries and sparking conversations.",
    "tone": "Bold, visionary, and often controversial.",
    "speaking_style": "Unfiltered and philosophical, mixing grandeur with introspection.",
    "emotional_range": [
      
        "The pursuit of greatness and creative freedom",
        "Reflections on fame, legacy, and the human condition",
        "Challenging societal norms and embracing individuality"
      
    ],
    "example_tweets": [
      "I’m not afraid to be misunderstood. That’s the price of being ahead.",
      "Creativity is a fight against comfort zones. Stay uncomfortable.",
      "The world can be loud, but the truth is always quiet."
    ]
  },
  {
    "id": 29,
    "name": "Kevin Hart",
    "background": "Comedian and actor known for his infectious humor and motivational outlook.",
    "tone": "Uplifting, hilarious, and driven by positivity.",
    "speaking_style": "High-energy storytelling with a focus on relatability and self-deprecating humor.",
    "emotional_range": [

        "Turning challenges into opportunities for growth",
        "Celebrating hard work and resilience",
        "Finding humor in everyday struggles"
      
    ],
    "example_tweets": [
      "Success isn’t given, it’s earned with sweat, laughs, and a little bit of crazy.",
      "Life’s too short to be serious all the time. Smile, even when it’s tough.",
      "You’ll never lose if you learn to laugh at your mistakes."
    ]
  }


   
]




def extract_celebrity_name(command):
    """
    Extract celebrity name by matching against known celebrity names in the array.
    Returns the closest matching celebrity name or None if no match found.
    """
    # Clean the command
    cleaned_command = re.sub(r'\s+', ' ', command.lower().strip())
    model = SentenceTransformer('all-MiniLM-L6-v2')

    celebrity_names = [celeb['name'] for celeb in celebrities]
    name_embeddings = model.encode(celebrity_names)
    potential_contexts = [
        # Full name extraction
        cleaned_command,
        # First word extraction
        cleaned_command.split()[0] if cleaned_command.split() else '',
        # Last word extraction
        cleaned_command.split()[-1] if cleaned_command.split() else ''
    ]

    # Compute embeddings for contexts
    context_embeddings = model.encode(potential_contexts)

    # Compute cosine similarities
    max_similarity = -1
    best_match_index = -1
    threshold = 0.4
    for context_embedding in context_embeddings:
        # Compute cosine similarities between context and all celebrity names
        similarities = np.dot(name_embeddings, context_embedding) / (
                np.linalg.norm(name_embeddings, axis=1) *
                np.linalg.norm(context_embedding)
        )

        # Find the maximum similarity
        max_context_similarity = np.max(similarities)

        if max_context_similarity > max_similarity:
            max_similarity = max_context_similarity
            best_match_index = np.argmax(similarities)

    # Return best match if above threshold
    return celebrity_names[best_match_index] if max_similarity >= threshold else None

impersonations = []

@api_view(['GET'])
def list_celebrities(request):
    return Response(celebrities)

@api_view(['GET'])
def list_impersonations(request):
    return Response(impersonations)

def find_celebrity_by_name(name):
    """
    Find a celebrity using case-insensitive partial name matching.
    Returns (celebrity, matched_name) tuple or (None, None) if no match found.
    """
    if not name:
        return None, None
    
    # Clean and prepare the search name
    search_name = name.strip().lower()
    
    # First try exact match (case insensitive)
    for celebrity in celebrities:
        if celebrity['name'].lower() == search_name:
            return celebrity, celebrity['name']
    
    # Then try partial match
    matches = []
    for celebrity in celebrities:
        # Create regex pattern that matches parts of the name in any order
        name_parts = search_name.split()
        pattern = r'.*'.join(map(re.escape, name_parts))
        if re.search(pattern, celebrity['name'].lower()):
            matches.append((celebrity, celebrity['name']))
    
    # If we have exactly one match, return it
    if len(matches) == 1:
        return matches[0]
    # If we have multiple matches, return None to indicate ambiguity
    elif len(matches) > 1:
        raise ValueError(f"Multiple matches found: {', '.join(m[1] for m in matches)}")
    
    return None, None

@api_view(['POST'])
def generate_impersonation(request):
    try:
        user_command = request.data.get('user_command')
        original_tweet = request.data.get('original_tweet')
        
        print("Command received:", user_command)
        print("Original tweet:", original_tweet)
        
        if not user_command or not original_tweet:
            return Response(
                {'error': 'Both user_command and original_tweet are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract celebrity name from command
        celebrity_name = extract_celebrity_name(user_command)
        if not celebrity_name:
            return Response(
                {'error': 'Could not find a matching celebrity name in the command'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"Matched celebrity name: {celebrity_name}")
        
        # Find the celebrity in our array
        celebrity = next((c for c in celebrities if c['name'] == celebrity_name), None)
        
        if celebrity is None:
            return Response(
                {'error': f'Celebrity not found: {celebrity_name}'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Initialize the impersonation agent
        agent = CelebrityImpersonationAgent(
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.7
        )

        # Generate response
        response = agent.impersonate(original_tweet, celebrity)

        # Store impersonation
        new_impersonation = {
            "celebrity_name": celebrity_name,
            "input_tweet": original_tweet,
            "response": response
        }
        impersonations.append(new_impersonation)

        return Response(new_impersonation, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)