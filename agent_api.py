import os
import base64

from dotenv import load_dotenv
# import uvicorn
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
from flask import Flask, request, jsonify

from openai import OpenAI
from nova_act import NovaAct

from agent_find_product import ask_nova_search_product_agent
from agent_add_to_cart import ask_nova_add_it_to_cart_agent
from agent_search_similar_products import ask_nova_search_similar_agent

from api_docs.agents import AddItRequest, AddItResponse, FindItRequest, FindItResponse, SearchSimilarRequest, SearchSimilarResponse

load_dotenv()


NOVA_ACT_API_KEY = os.getenv("NOVA_ACT_API_KEY")
NOVA_BASE_URL = os.getenv("NOVA_BASE_URL", "https://api.nova.amazon.com/v1")
PROFILE_DIR = "./nova_profile"
TMP_PATH = "./tmp_images/"
START_PAGE = "https://www.amazon.ca/"


# app = FastAPI(title="NovaAct Agents BackstageCommerce API")
app = Flask(__name__)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

client = OpenAI(
    api_key=NOVA_ACT_API_KEY,
    base_url=NOVA_BASE_URL,
)


def to_data_url(path: str, mime_type: str = "image/jpeg") -> str:
    with open(TMP_PATH + path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"

def call_nova(body, agent: str = "add_it_to_shopping_cart", *args, **kwargs):
    nova = NovaAct(
        starting_page=START_PAGE,
        nova_act_api_key=NOVA_ACT_API_KEY,
        user_data_dir=PROFILE_DIR,
        clone_user_data_dir=False,
    )
    nova.start()
    result = False
    if agent == "add_it_to_shopping_cart":
        result = ask_nova_add_it_to_cart_agent(nova, body, add_to_wishlist=kwargs.get('add_to_wishlist', ''))
    elif agent == "select_similar_from_amazon":
        result = ask_nova_search_similar_agent(nova, body, k=kwargs.get('k', 1), add_to_wishlist=kwargs.get('add_to_wishlist', ''))
    nova.stop()
    return result

@app.post("/find-it-on-amazon")
def find_it_on_amazon():
    data = request.get_json()
    frame = data.get("image_data", None)
    frame_url = data.get("image_url", None)
    # if not frame and frame_url:
    #     retrieve_image_from_url(frame_url)
    # else:

    # frame_url is frame_name in the tmp directory
    frame = to_data_url(frame_url, "image/jpeg")
    text_prompt = data.get("user_prompt", None)

    return ask_nova_search_product_agent(client, input_image=frame, text_prompt=text_prompt)

@app.post("/select-similar-from-amazon")
def select_similar_from_amazon():
    data = request.get_json()
    product_description = data.get("product_description", None)
    return {"amazon_links": call_nova(product_description, "select_similar_from_amazon", add_to_wishlist='', k=2)}

@app.post("/select-similar-from-amazon/add_to_list")
def select_similar_from_amazon_and_add_to_list():
    data = request.get_json()
    list_name = data.get('list_name', 'wishlist')
    product_description = data.get("product_description", None)
    return {"amazon_links": call_nova(product_description, "select_similar_from_amazon", add_to_wishlist=f'Add product to the "{list_name}".', k=1)}


@app.route("/add-it-to-shopping-cart", methods=["POST"])
def add_it_to_shopping_cart():
    data = request.get_json()
    return {"agent_finished": call_nova(data.get("product_url", None), "add_it_to_shopping_cart")}

@app.route("/add-it-to-shopping-list", methods=["POST"])
def add_it_to_shopping_list():
    data = request.get_json()
    list_name = data.get('list_name', 'wishlist')
    return {"agent_finished": call_nova(data.get("product_url", None), "add_it_to_shopping_cart", add_to_wishlist=f'Add product to the "{list_name}".')}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)