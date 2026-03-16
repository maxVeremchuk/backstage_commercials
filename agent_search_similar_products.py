import os
from dotenv import load_dotenv
load_dotenv()

AGENT_NAME = os.getenv('AGENT_SEARCH_SIMILAR_ID')

def ask_nova_search_similar_agent(nova, product_description: str, k: int = 2, add_to_wishlist: str = 'Add product to the "wishlist".') -> list[str]:
    urls = []
    for _ in range(k):
        nova.act(f'Insert this to Amazon search: {product_description} . Find an item that fits the description, if you are already on the product page for the item, search for the next similar one. Open the product page. {add_to_wishlist}')
        current_url = nova.page.url
        urls.append(current_url)
    return urls
