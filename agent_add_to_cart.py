def ask_nova_add_it_to_cart_agent(nova, product_url: str) -> bool:
    # Hack to log into your Amazon profile:
    # make an agent wait, while you insert your creds manually,
    # then it saves logging info to the cached dir and you'll be logged in the next run
    # time.sleep(20)
    nova.act(f"Go to this URL: {product_url} . Add item to the cart.")
    return True
