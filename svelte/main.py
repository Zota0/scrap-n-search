from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3

class WebContent:
    def __init__(self, url, content, timestamp, metadata=None):
        self.url = url
        self.content = content
        self.timestamp = timestamp
        self.metadata = metadata or {}

class AISearchSystem:
    def __init__(self):
        self.content_store = []
        
    def store_content(self, web_content):
        """Store WebContent object in the system"""
        self.content_store.append(web_content)
        
    from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3
from typing import List, Dict

class WebContent:
    def __init__(self, url, content, timestamp, metadata=None):
        self.url = url
        self.content = content
        self.timestamp = timestamp
        self.metadata = metadata or {}

class AISearchSystem:
    def __init__(self):
        self.content_store = []
        
    def store_content(self, web_content):
        """Store WebContent object in the system"""
        self.content_store.append(web_content)
        
    def semantic_search(self, query: str) -> Dict:
        """Enhanced search implementation with structured response"""
        results = []
        query_terms = query.lower().split()
        
        for content in self.content_store:
            score = 0
            content_text = content.content.lower()
            
            # Simple scoring based on term frequency
            for term in query_terms:
                score += content_text.count(term)
                
            if score > 0:
                # Calculate similarity score (normalized between 0 and 1)
                max_possible_score = len(query_terms) * (len(content_text.split()) / 10)  # rough estimation
                similarity = min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0
                
                # Create summary (first 200 chars)
                summary = content.content[:200].strip() + "..."
                
                # Extract key points (simple implementation)
                sentences = content.content.split('.')
                key_points = [s.strip() for s in sentences[:3] if len(s.strip()) > 20]
                
                results.append({
                    'url': content.url,
                    'title': content.metadata.get('title', content.url),
                    'similarity': similarity,
                    'summary': summary,
                    'key_points': key_points,
                    'chunk': content.content[:200] + '...'  # Fallback content
                })
        
        # Sort results by similarity score
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Generate overall summary
        overall_summary = "Found {} relevant results. ".format(len(results))
        if results:
            overall_summary += "Most relevant content from {} and other sources.".format(
                results[0]['title']
            )
        
        return {
            'results': results,
            'overall_summary': overall_summary
        }

class DataLoader:
    def __init__(self, search_system):
        self.search_system = search_system
        self.db_path = "url_cache.db"
        self._init_cache_db()
        
    def _init_cache_db(self):
        """Initialize SQLite database to track scraped URLs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scraped_urls (
                    url TEXT PRIMARY KEY,
                    timestamp TIMESTAMP,
                    success BOOLEAN
                )
            """)
            
    def is_url_scraped(self, url: str) -> bool:
        """Check if URL has already been scraped"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT timestamp FROM scraped_urls WHERE url = ? AND success = 1", 
                (url,)
            )
            return cursor.fetchone() is not None
            
    def mark_url_scraped(self, url: str, success: bool = True):
        """Mark URL as scraped in the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO scraped_urls (url, timestamp, success) VALUES (?, ?, ?)",
                (url, datetime.now(), success)
            )
        
    def scrape_and_store_url(self, url: str, force_refresh: bool = False):
        """Scrape content from a URL and store it in the search system"""
        # Skip if already scraped and not forcing refresh
        if not force_refresh and self.is_url_scraped(url):
            print(f"Skipping already scraped URL: {url}")
            return None
            
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get title
            title = soup.title.string if soup.title else url
            
            # Extract text and clean it up
            text = ' '.join(soup.stripped_strings)
            
            web_content = WebContent(
                url=url,
                content=text,
                timestamp=datetime.now(),
                metadata={
                    'title': title,
                    'tags': ['webpage']
                }
            )
            
            # Store the content in the search system
            self.search_system.store_content(web_content)
            
            # Mark URL as successfully scraped
            self.mark_url_scraped(url, success=True)
            
            print(f"Successfully scraped and stored: {url}")
            return web_content
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            # Mark URL as failed
            self.mark_url_scraped(url, success=False)
            return None
            
    def load_initial_data(self, force_refresh: bool = False):
        """Load initial data into the search system"""
        # Add some sample content
        sample_content = WebContent(
            url="local://sample",
            content="""
            This is a sample document about artificial intelligence and search systems.
            AI systems can process and understand natural language queries.
            They use advanced algorithms to find relevant information quickly.
            Machine learning models help improve search results over time.
            Neural networks and deep learning are key components of modern AI systems.
            Search engines use sophisticated ranking algorithms to show the most relevant results.
            Natural Language Processing (NLP) helps computers understand human language.
            """,
            timestamp=datetime.now(),
            metadata={
                'title': "Introduction to AI Search",
                'tags': ['AI', 'search', 'sample']
            }
        )
        self.search_system.store_content(sample_content)
        print("Added sample content")
        
        # Add technical sample
        technical_content = WebContent(
            url="local://technical",
            content="""
            Python is a versatile programming language widely used in AI development.
            It offers many libraries like TensorFlow and PyTorch for machine learning.
            Web servers can be built using frameworks like Flask and Django.
            Database systems store and retrieve information efficiently.
            APIs enable different systems to communicate and share data.
            """,
            timestamp=datetime.now(),
            metadata={
                'title': "Technical Overview",
                'tags': ['programming', 'technology', 'sample']
            }
        )
        self.search_system.store_content(technical_content)
        print("Added technical content")
        
        # Add your URLs here
        urls = [
            "https://svelte.dev/","https://svelte.dev/#main","https://svelte.dev/blog","https://svelte.dev/chat","https://svelte.dev/docs","https://svelte.dev/docs#main","https://svelte.dev/docs/cli","https://svelte.dev/docs/cli/","https://svelte.dev/docs/cli/#Acknowledgements","https://svelte.dev/docs/cli/#Usage","https://svelte.dev/docs/cli/#main","https://svelte.dev/docs/cli/overview","https://svelte.dev/docs/cli/sv-add","https://svelte.dev/docs/cli/sv-check","https://svelte.dev/docs/cli/sv-create","https://svelte.dev/docs/cli/sv-migrate","https://svelte.dev/docs/kit","https://svelte.dev/docs/kit#main","https://svelte.dev/docs/kit/","https://svelte.dev/docs/kit/#Before-we-begin","https://svelte.dev/docs/kit/#SvelteKit-vs-Svelte","https://svelte.dev/docs/kit/#What-is-Svelte","https://svelte.dev/docs/kit/#What-is-SvelteKit","https://svelte.dev/docs/kit/#main","https://svelte.dev/docs/kit/$app-environment","https://svelte.dev/docs/kit/$app-forms","https://svelte.dev/docs/kit/$app-navigation","https://svelte.dev/docs/kit/$app-paths","https://svelte.dev/docs/kit/$app-server","https://svelte.dev/docs/kit/$app-stores","https://svelte.dev/docs/kit/$env-dynamic-private","https://svelte.dev/docs/kit/$env-dynamic-public","https://svelte.dev/docs/kit/$env-static-private","https://svelte.dev/docs/kit/$env-static-public","https://svelte.dev/docs/kit/$lib","https://svelte.dev/docs/kit/$service-worker","https://svelte.dev/docs/kit/@sveltejs-kit","https://svelte.dev/docs/kit/@sveltejs-kit-hooks","https://svelte.dev/docs/kit/@sveltejs-kit-node","https://svelte.dev/docs/kit/@sveltejs-kit-node-polyfills","https://svelte.dev/docs/kit/@sveltejs-kit-vite","https://svelte.dev/docs/kit/accessibility","https://svelte.dev/docs/kit/adapter-auto","https://svelte.dev/docs/kit/adapter-cloudflare","https://svelte.dev/docs/kit/adapter-cloudflare-workers","https://svelte.dev/docs/kit/adapter-netlify","https://svelte.dev/docs/kit/adapter-node","https://svelte.dev/docs/kit/adapter-static","https://svelte.dev/docs/kit/adapter-vercel","https://svelte.dev/docs/kit/adapters","https://svelte.dev/docs/kit/additional-resources","https://svelte.dev/docs/kit/advanced-routing","https://svelte.dev/docs/kit/auth","https://svelte.dev/docs/kit/building-your-app","https://svelte.dev/docs/kit/cli","https://svelte.dev/docs/kit/configuration","https://svelte.dev/docs/kit/creating-a-project","https://svelte.dev/docs/kit/debugging","https://svelte.dev/docs/kit/errors","https://svelte.dev/docs/kit/faq","https://svelte.dev/docs/kit/faq#What-can-I-make-with-SvelteKit","https://svelte.dev/docs/kit/form-actions","https://svelte.dev/docs/kit/glossary","https://svelte.dev/docs/kit/glossary#CSR","https://svelte.dev/docs/kit/glossary#Prerendering","https://svelte.dev/docs/kit/glossary#Routing","https://svelte.dev/docs/kit/glossary#SSR","https://svelte.dev/docs/kit/hooks","https://svelte.dev/docs/kit/images","https://svelte.dev/docs/kit/integrations","https://svelte.dev/docs/kit/introduction","https://svelte.dev/docs/kit/link-options","https://svelte.dev/docs/kit/link-options#data-sveltekit-preload-data","https://svelte.dev/docs/kit/load","https://svelte.dev/docs/kit/migrating","https://svelte.dev/docs/kit/migrating-to-sveltekit-2","https://svelte.dev/docs/kit/packaging","https://svelte.dev/docs/kit/page-options","https://svelte.dev/docs/kit/performance","https://svelte.dev/docs/kit/project-structure","https://svelte.dev/docs/kit/routing","https://svelte.dev/docs/kit/seo","https://svelte.dev/docs/kit/server-only-modules","https://svelte.dev/docs/kit/service-workers","https://svelte.dev/docs/kit/shallow-routing","https://svelte.dev/docs/kit/single-page-apps","https://svelte.dev/docs/kit/snapshots","https://svelte.dev/docs/kit/state-management","https://svelte.dev/docs/kit/types","https://svelte.dev/docs/kit/web-standards","https://svelte.dev/docs/kit/writing-adapters","https://svelte.dev/docs/svelte","https://svelte.dev/docs/svelte#main","https://svelte.dev/docs/svelte/$bindable","https://svelte.dev/docs/svelte/$derived","https://svelte.dev/docs/svelte/$effect","https://svelte.dev/docs/svelte/$host","https://svelte.dev/docs/svelte/$inspect","https://svelte.dev/docs/svelte/$props","https://svelte.dev/docs/svelte/$state","https://svelte.dev/docs/svelte/@const","https://svelte.dev/docs/svelte/@debug","https://svelte.dev/docs/svelte/@html","https://svelte.dev/docs/svelte/@render","https://svelte.dev/docs/svelte/animate","https://svelte.dev/docs/svelte/await","https://svelte.dev/docs/svelte/basic-markup","https://svelte.dev/docs/svelte/bind","https://svelte.dev/docs/svelte/class","https://svelte.dev/docs/svelte/compiler-errors","https://svelte.dev/docs/svelte/compiler-warnings","https://svelte.dev/docs/svelte/context","https://svelte.dev/docs/svelte/custom-elements","https://svelte.dev/docs/svelte/custom-properties","https://svelte.dev/docs/svelte/each","https://svelte.dev/docs/svelte/faq","https://svelte.dev/docs/svelte/getting-started","https://svelte.dev/docs/svelte/global-styles","https://svelte.dev/docs/svelte/if","https://svelte.dev/docs/svelte/imperative-component-api","https://svelte.dev/docs/svelte/in-and-out","https://svelte.dev/docs/svelte/key","https://svelte.dev/docs/svelte/legacy-$$props-and-$$restProps","https://svelte.dev/docs/svelte/legacy-$$slots","https://svelte.dev/docs/svelte/legacy-component-api","https://svelte.dev/docs/svelte/legacy-export-let","https://svelte.dev/docs/svelte/legacy-let","https://svelte.dev/docs/svelte/legacy-on","https://svelte.dev/docs/svelte/legacy-overview","https://svelte.dev/docs/svelte/legacy-reactive-assignments","https://svelte.dev/docs/svelte/legacy-slots","https://svelte.dev/docs/svelte/legacy-svelte-component","https://svelte.dev/docs/svelte/legacy-svelte-fragment","https://svelte.dev/docs/svelte/legacy-svelte-self","https://svelte.dev/docs/svelte/lifecycle-hooks","https://svelte.dev/docs/svelte/nested-style-elements","https://svelte.dev/docs/svelte/overview","https://svelte.dev/docs/svelte/runtime-errors","https://svelte.dev/docs/svelte/runtime-warnings","https://svelte.dev/docs/svelte/scoped-styles","https://svelte.dev/docs/svelte/snippet","https://svelte.dev/docs/svelte/stores","https://svelte.dev/docs/svelte/style","https://svelte.dev/docs/svelte/svelte","https://svelte.dev/docs/svelte/svelte-action","https://svelte.dev/docs/svelte/svelte-animate","https://svelte.dev/docs/svelte/svelte-body","https://svelte.dev/docs/svelte/svelte-compiler","https://svelte.dev/docs/svelte/svelte-document","https://svelte.dev/docs/svelte/svelte-easing","https://svelte.dev/docs/svelte/svelte-element","https://svelte.dev/docs/svelte/svelte-events","https://svelte.dev/docs/svelte/svelte-files","https://svelte.dev/docs/svelte/svelte-head","https://svelte.dev/docs/svelte/svelte-js-files","https://svelte.dev/docs/svelte/svelte-legacy","https://svelte.dev/docs/svelte/svelte-motion","https://svelte.dev/docs/svelte/svelte-options","https://svelte.dev/docs/svelte/svelte-reactivity","https://svelte.dev/docs/svelte/svelte-server","https://svelte.dev/docs/svelte/svelte-store","https://svelte.dev/docs/svelte/svelte-transition","https://svelte.dev/docs/svelte/svelte-window","https://svelte.dev/docs/svelte/testing","https://svelte.dev/docs/svelte/transition","https://svelte.dev/docs/svelte/typescript","https://svelte.dev/docs/svelte/use","https://svelte.dev/docs/svelte/v4-migration-guide","https://svelte.dev/docs/svelte/v5-migration-guide","https://svelte.dev/docs/svelte/what-are-runes","https://svelte.dev/kit","https://svelte.dev/playground","https://svelte.dev/tutorial","https://svelte.dev/tutorial/kit","https://tailwindcss.com/","https://tailwindcss.com/blog","https://tailwindcss.com/blog/2024-05-24-catalyst-application-layouts","https://tailwindcss.com/docs","https://tailwindcss.com/docs/adding-custom-styles","https://tailwindcss.com/docs/align-content","https://tailwindcss.com/docs/align-items","https://tailwindcss.com/docs/align-self","https://tailwindcss.com/docs/aspect-ratio","https://tailwindcss.com/docs/box-decoration-break","https://tailwindcss.com/docs/box-sizing","https://tailwindcss.com/docs/break-after","https://tailwindcss.com/docs/break-before","https://tailwindcss.com/docs/break-inside","https://tailwindcss.com/docs/browser-support","https://tailwindcss.com/docs/clear","https://tailwindcss.com/docs/columns","https://tailwindcss.com/docs/configuration","https://tailwindcss.com/docs/container","https://tailwindcss.com/docs/content-configuration","https://tailwindcss.com/docs/customizing-colors","https://tailwindcss.com/docs/customizing-spacing","https://tailwindcss.com/docs/dark-mode","https://tailwindcss.com/docs/display","https://tailwindcss.com/docs/editor-setup","https://tailwindcss.com/docs/flex","https://tailwindcss.com/docs/flex-basis","https://tailwindcss.com/docs/flex-direction","https://tailwindcss.com/docs/flex-grow","https://tailwindcss.com/docs/flex-shrink","https://tailwindcss.com/docs/flex-wrap","https://tailwindcss.com/docs/float","https://tailwindcss.com/docs/font-family","https://tailwindcss.com/docs/font-size","https://tailwindcss.com/docs/font-smoothing","https://tailwindcss.com/docs/font-style","https://tailwindcss.com/docs/font-variant-numeric","https://tailwindcss.com/docs/font-weight","https://tailwindcss.com/docs/functions-and-directives","https://tailwindcss.com/docs/gap","https://tailwindcss.com/docs/grid-auto-columns","https://tailwindcss.com/docs/grid-auto-flow","https://tailwindcss.com/docs/grid-auto-rows","https://tailwindcss.com/docs/grid-column","https://tailwindcss.com/docs/grid-row","https://tailwindcss.com/docs/grid-template-columns","https://tailwindcss.com/docs/grid-template-rows","https://tailwindcss.com/docs/height","https://tailwindcss.com/docs/hover-focus-and-other-states","https://tailwindcss.com/docs/installation","https://tailwindcss.com/docs/isolation","https://tailwindcss.com/docs/justify-content","https://tailwindcss.com/docs/justify-items","https://tailwindcss.com/docs/justify-self","https://tailwindcss.com/docs/letter-spacing","https://tailwindcss.com/docs/line-clamp","https://tailwindcss.com/docs/line-height","https://tailwindcss.com/docs/list-style-image","https://tailwindcss.com/docs/list-style-position","https://tailwindcss.com/docs/list-style-type","https://tailwindcss.com/docs/margin","https://tailwindcss.com/docs/max-height","https://tailwindcss.com/docs/max-width","https://tailwindcss.com/docs/min-height","https://tailwindcss.com/docs/min-width","https://tailwindcss.com/docs/object-fit","https://tailwindcss.com/docs/object-position","https://tailwindcss.com/docs/optimizing-for-production","https://tailwindcss.com/docs/order","https://tailwindcss.com/docs/overflow","https://tailwindcss.com/docs/overscroll-behavior","https://tailwindcss.com/docs/padding","https://tailwindcss.com/docs/place-content","https://tailwindcss.com/docs/place-items","https://tailwindcss.com/docs/place-self","https://tailwindcss.com/docs/plugins","https://tailwindcss.com/docs/position","https://tailwindcss.com/docs/preflight","https://tailwindcss.com/docs/presets","https://tailwindcss.com/docs/responsive-design","https://tailwindcss.com/docs/reusing-styles","https://tailwindcss.com/docs/screens","https://tailwindcss.com/docs/size","https://tailwindcss.com/docs/space","https://tailwindcss.com/docs/text-align","https://tailwindcss.com/docs/text-color","https://tailwindcss.com/docs/text-decoration","https://tailwindcss.com/docs/text-decoration-color","https://tailwindcss.com/docs/text-decoration-style","https://tailwindcss.com/docs/text-decoration-thickness","https://tailwindcss.com/docs/theme","https://tailwindcss.com/docs/top-right-bottom-left","https://tailwindcss.com/docs/upgrade-guide","https://tailwindcss.com/docs/using-with-preprocessors","https://tailwindcss.com/docs/utility-first","https://tailwindcss.com/docs/visibility","https://tailwindcss.com/docs/width","https://tailwindcss.com/docs/z-index","https://tailwindcss.com/resources","https://tailwindcss.com/showcase","https://www.typescriptlang.org/","https://www.typescriptlang.org/#","https://www.typescriptlang.org/#m-stories","https://www.typescriptlang.org/#site-content","https://www.typescriptlang.org/assets/typescript-cheat-sheets.zip","https://www.typescriptlang.org/branding/","https://www.typescriptlang.org/cheatsheets/","https://www.typescriptlang.org/community","https://www.typescriptlang.org/community/","https://www.typescriptlang.org/docs/","https://www.typescriptlang.org/docs/#site-content","https://www.typescriptlang.org/docs/handbook/2/basic-types.html","https://www.typescriptlang.org/docs/handbook/2/classes.html","https://www.typescriptlang.org/docs/handbook/2/conditional-types.html","https://www.typescriptlang.org/docs/handbook/2/everyday-types.html","https://www.typescriptlang.org/docs/handbook/2/functions.html","https://www.typescriptlang.org/docs/handbook/2/generics.html","https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html","https://www.typescriptlang.org/docs/handbook/2/keyof-types.html","https://www.typescriptlang.org/docs/handbook/2/mapped-types.html","https://www.typescriptlang.org/docs/handbook/2/modules.html","https://www.typescriptlang.org/docs/handbook/2/narrowing.html","https://www.typescriptlang.org/docs/handbook/2/objects.html","https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html","https://www.typescriptlang.org/docs/handbook/2/typeof-types.html","https://www.typescriptlang.org/docs/handbook/2/types-from-types.html","https://www.typescriptlang.org/docs/handbook/asp-net-core.html","https://www.typescriptlang.org/docs/handbook/babel-with-typescript.html","https://www.typescriptlang.org/docs/handbook/compiler-options-in-msbuild.html","https://www.typescriptlang.org/docs/handbook/compiler-options.html","https://www.typescriptlang.org/docs/handbook/configuring-watch.html","https://www.typescriptlang.org/docs/handbook/declaration-files/by-example.html","https://www.typescriptlang.org/docs/handbook/declaration-files/consumption.html","https://www.typescriptlang.org/docs/handbook/declaration-files/deep-dive.html","https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html","https://www.typescriptlang.org/docs/handbook/declaration-files/dts-from-js.html","https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html","https://www.typescriptlang.org/docs/handbook/declaration-files/library-structures.html","https://www.typescriptlang.org/docs/handbook/declaration-files/publishing.html","https://www.typescriptlang.org/docs/handbook/declaration-files/templates/global-d-ts.html","https://www.typescriptlang.org/docs/handbook/declaration-files/templates/global-modifying-module-d-ts.html","https://www.typescriptlang.org/docs/handbook/declaration-files/templates/module-class-d-ts.html","https://www.typescriptlang.org/docs/handbook/declaration-files/templates/module-d-ts.html","https://www.typescriptlang.org/docs/handbook/declaration-files/templates/module-function-d-ts.html","https://www.typescriptlang.org/docs/handbook/declaration-files/templates/module-plugin-d-ts.html","https://www.typescriptlang.org/docs/handbook/declaration-merging.html","https://www.typescriptlang.org/docs/handbook/decorators.html","https://www.typescriptlang.org/docs/handbook/dom-manipulation.html","https://www.typescriptlang.org/docs/handbook/enums.html","https://www.typescriptlang.org/docs/handbook/gulp.html","https://www.typescriptlang.org/docs/handbook/integrating-with-build-tools.html","https://www.typescriptlang.org/docs/handbook/intro-to-js-ts.html","https://www.typescriptlang.org/docs/handbook/intro.html","https://www.typescriptlang.org/docs/handbook/intro.html#handbook-content","https://www.typescriptlang.org/docs/handbook/iterators-and-generators.html","https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html","https://www.typescriptlang.org/docs/handbook/jsx.html","https://www.typescriptlang.org/docs/handbook/migrating-from-javascript.html","https://www.typescriptlang.org/docs/handbook/mixins.html","https://www.typescriptlang.org/docs/handbook/modules/appendices/esm-cjs-interop.html","https://www.typescriptlang.org/docs/handbook/modules/guides/choosing-compiler-options.html","https://www.typescriptlang.org/docs/handbook/modules/introduction.html","https://www.typescriptlang.org/docs/handbook/modules/reference.html","https://www.typescriptlang.org/docs/handbook/modules/theory.html","https://www.typescriptlang.org/docs/handbook/namespaces-and-modules.html","https://www.typescriptlang.org/docs/handbook/namespaces.html","https://www.typescriptlang.org/docs/handbook/nightly-builds.html","https://www.typescriptlang.org/docs/handbook/project-references.html","https://www.typescriptlang.org/docs/handbook/react-&-webpack.html","https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-2.html","https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-3.html","https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-4.html","https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-5.html","https://www.typescriptlang.org/docs/handbook/symbols.html","https://www.typescriptlang.org/docs/handbook/triple-slash-directives.html","https://www.typescriptlang.org/docs/handbook/tsconfig-json.html","https://www.typescriptlang.org/docs/handbook/type-checking-javascript-files.html","https://www.typescriptlang.org/docs/handbook/type-compatibility.html","https://www.typescriptlang.org/docs/handbook/type-inference.html","https://www.typescriptlang.org/docs/handbook/typescript-from-scratch.html","https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes-func.html","https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes-oop.html","https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html","https://www.typescriptlang.org/docs/handbook/typescript-tooling-in-5-minutes.html","https://www.typescriptlang.org/docs/handbook/utility-types.html","https://www.typescriptlang.org/docs/handbook/variable-declarations.html","https://www.typescriptlang.org/download","https://www.typescriptlang.org/download/","https://www.typescriptlang.org/download/#site-content","https://www.typescriptlang.org/play","https://www.typescriptlang.org/play/","https://www.typescriptlang.org/play/#show-examples","https://www.typescriptlang.org/static/TypeScript%20Classes-83cc6f8e42ba2002d5e2c04221fa78f9.png","https://www.typescriptlang.org/static/TypeScript%20Control%20Flow%20Analysis-8a549253ad8470850b77c4c5c351d457.png","https://www.typescriptlang.org/static/TypeScript%20Interfaces-34f1ad12132fb463bd1dfe5b85c5b2e6.png","https://www.typescriptlang.org/static/TypeScript%20Types-ae199d69aeecf7d4a2704a528d0fd3f9.png","https://www.typescriptlang.org/tools/","https://www.typescriptlang.org/tsconfig/","https://www.typescriptlang.org/tsconfig/#isolatedModules","https://www.typescriptlang.org/why-create-typescript/","https://www.w3schools.com/","https://www.w3schools.com/academy/index.php","https://www.w3schools.com/academy/teachers/index.php","https://www.w3schools.com/accessibility/index.php","https://www.w3schools.com/ai/default.asp","https://www.w3schools.com/angular/angular_ref_directives.asp","https://www.w3schools.com/angular/default.asp","https://www.w3schools.com/appml/appml_reference.asp","https://www.w3schools.com/appml/default.asp","https://www.w3schools.com/asp/asp_ref_vbscript_functions.asp","https://www.w3schools.com/asp/default.asp","https://www.w3schools.com/aws/index.php","https://www.w3schools.com/bootstrap/bootstrap_ver.asp","https://www.w3schools.com/browsers/default.asp","https://www.w3schools.com/c/c_ref_reference.php","https://www.w3schools.com/c/index.php","https://www.w3schools.com/charsets/default.asp","https://www.w3schools.com/codegame/index.html","https://www.w3schools.com/colors/colors_fs595.asp","https://www.w3schools.com/colors/default.asp","https://www.w3schools.com/cpp/cpp_ref_reference.asp","https://www.w3schools.com/cpp/default.asp","https://www.w3schools.com/cs/index.php","https://www.w3schools.com/css","https://www.w3schools.com/css/css_rwd_intro.asp","https://www.w3schools.com/css/default.asp","https://www.w3schools.com/cssref/default.asp","https://www.w3schools.com/cybersecurity/index.php","https://www.w3schools.com/datascience/default.asp","https://www.w3schools.com/django/django_ref_template_tags.php","https://www.w3schools.com/django/index.php","https://www.w3schools.com/dsa/index.php","https://www.w3schools.com/excel/index.php","https://www.w3schools.com/gen_ai/bard/index.php","https://www.w3schools.com/gen_ai/chatgpt-3-5/index.php","https://www.w3schools.com/gen_ai/chatgpt-4/index.php","https://www.w3schools.com/gen_ai/index.php","https://www.w3schools.com/git/default.asp","https://www.w3schools.com/go/index.php","https://www.w3schools.com/googlesheets/index.php","https://www.w3schools.com/graphics/canvas_intro.asp","https://www.w3schools.com/graphics/canvas_reference.asp","https://www.w3schools.com/graphics/default.asp","https://www.w3schools.com/graphics/svg_intro.asp","https://www.w3schools.com/graphics/svg_reference.asp","https://www.w3schools.com/howto/default.asp","https://www.w3schools.com/html","https://www.w3schools.com/html/default.asp","https://www.w3schools.com/html/html_exercises.asp","https://www.w3schools.com/icons/default.asp","https://www.w3schools.com/icons/icons_reference.asp","https://www.w3schools.com/java/default.asp","https://www.w3schools.com/java/java_ref_reference.asp","https://www.w3schools.com/jquery/default.asp","https://www.w3schools.com/jquery/jquery_ref_overview.asp","https://www.w3schools.com/js/","https://www.w3schools.com/js/default.asp","https://www.w3schools.com/js/js_ajax_intro.asp","https://www.w3schools.com/js/js_json_intro.asp","https://www.w3schools.com/jsref/default.asp","https://www.w3schools.com/jsref/jsref_obj_json.asp","https://www.w3schools.com/kotlin/index.php","https://www.w3schools.com/mongodb/index.php","https://www.w3schools.com/mysql/default.asp","https://www.w3schools.com/mysql/mysql_datatypes.asp","https://www.w3schools.com/nodejs/default.asp","https://www.w3schools.com/nodejs/nodejs_raspberrypi.asp","https://www.w3schools.com/nodejs/ref_modules.asp","https://www.w3schools.com/php/default.asp","https://www.w3schools.com/php/php_ref_overview.asp","https://www.w3schools.com/plus/index.php","https://www.w3schools.com/postgresql/index.php","https://www.w3schools.com/python/default.asp","https://www.w3schools.com/python/matplotlib_intro.asp","https://www.w3schools.com/python/numpy/default.asp","https://www.w3schools.com/python/pandas/default.asp","https://www.w3schools.com/python/python_ml_getting_started.asp","https://www.w3schools.com/python/python_reference.asp","https://www.w3schools.com/python/scipy/index.php","https://www.w3schools.com/r/default.asp","https://www.w3schools.com/react/default.asp","https://www.w3schools.com/sass/default.php","https://www.w3schools.com/sass/sass_functions_string.php","https://www.w3schools.com/spaces/index.php","https://www.w3schools.com/sql","https://www.w3schools.com/sql/default.asp","https://www.w3schools.com/sql/sql_ref_keywords.asp","https://www.w3schools.com/statistics/index.php","https://www.w3schools.com/tags/default.asp","https://www.w3schools.com/tryit/default.asp","https://www.w3schools.com/typescript","https://www.w3schools.com/typescript/index.php","https://www.w3schools.com/typingspeed/default.asp","https://www.w3schools.com/vue/index.php","https://www.w3schools.com/vue/vue_ref_builtin-attributes.php","https://www.w3schools.com/w3css/default.asp","https://www.w3schools.com/w3css/w3css_references.asp","https://www.w3schools.com/w3css/w3css_templates.asp","https://www.w3schools.com/w3js/default.asp","https://www.w3schools.com/w3js/w3js_references.asp","https://www.w3schools.com/whatis/default.asp","https://www.w3schools.com/where_to_start.asp","https://www.w3schools.com/xml/default.asp","https://www.w3schools.com/xml/dom_nodetype.asp"
        ]
        
        for url in urls:
            self.scrape_and_store_url(url, force_refresh=force_refresh)

class AISearchHandler(SimpleHTTPRequestHandler):
    search_system = AISearchSystem()

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == '/':
            # Serve index.html
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
            try:
                with open(template_path, 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.wfile.write(b"Error: index.html not found")
        else:
            # Handle other static files
            try:
                super().do_GET()
            except Exception as e:
                self.send_error(404, f"File not found: {str(e)}")

    def do_POST(self):
        if self.path == '/search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            query = data.get('query', '')

            try:
                results = self.search_system.semantic_search(query)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._send_cors_headers()
                self.end_headers()
                
                response = json.dumps(results)
                self.wfile.write(response.encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Search error: {str(e)}")

def run_server(port=9586):
    # Initialize the search system
    search_system = AISearchSystem()
    
    # Load initial data
    print("Loading initial data...")
    loader = DataLoader(search_system)
    loader.load_initial_data()
    
    # Set up the server
    server_address = ('', port)
    AISearchHandler.search_system = search_system  # Share the search system instance
    handler = AISearchHandler
    handler.extensions_map = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '': 'application/octet-stream',
    }
    
    httpd = HTTPServer(server_address, handler)
    print(f"Server running on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    # Initialize system and create required directories
    os.makedirs(os.path.join(os.path.dirname(__file__), "templates"), exist_ok=True)
    
    # Start the server
    print("Database initialized and ready")
    run_server(port=9586)