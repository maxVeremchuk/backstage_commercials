def ask_nova_add_it_to_cart_agent(nova, product_url: str, add_to_wishlist: str='') -> bool:
    # Hack to log into your Amazon profile:
    # make an agent wait, while you insert your creds manually,
    # then it saves logging info to the cached dir and you'll be logged in the next run
    # import time
    # time.sleep(20)
    nova.act(f"Go to this URL: {product_url} . Add the item to the {'cart' if not add_to_wishlist else add_to_wishlist}.")
    return True
