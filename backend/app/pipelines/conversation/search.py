import json

from app.genai.llm import llm_agent
from crawler.crawler import EcommerceRecommender

with open("app/genai/llm/prompts/Tasha/system.txt", "r") as file:
    SYSTEM_PROMPT = file.read()

tools = [
    {
        "type": "function",
        "name": "search_product",
        "description": "Search eCommerce sites for products matching a given query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The product name or keyword to search for. Must be in English",
                },
                "sort_by": {
                    "type": ["string", "null"],
                    "enum": ["price_asc", "price_desc", "popularity", "rating"],
                    "description": "How to sort the product results. Pass null if not needed.",
                },
            },
            "required": ["query", "sort_by"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "respond_customer",
        "description": "Respond to the customer's query.",
        "parameters": {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "The response to the customer's query. In the language of the customer.",
                },
            },
            "required": ["response"],
            "additionalProperties": False,
        },
    },
]


async def llm_search_product(query: str, message_history: list[dict]) -> str:
    recommender = None
    response_text = None
    message_history.append({"role": "user", "content": query})
    while response_text is None:
        response = llm_agent._generate_tool_call_response(
            message_history, tools, SYSTEM_PROMPT
        )
        if len(response.output_text) > 0:
            print("Normal output text")
            response_text = response.output_text
        else:
            tool_call = response.output[0]
            args = json.loads(tool_call.arguments)
            function_name = tool_call.name
            if function_name == "search_product":
                if recommender is None:
                    recommender = EcommerceRecommender()
                print(f"Searching for {args['query']}...")
                products = await recommender.crawl_for_products(args["query"])
                print(products)

                response_text = None
                message_history.append(tool_call)
                message_history.append(
                    {  # append result message
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": str(products),
                    }
                )
            elif function_name == "respond_customer":
                response_text = args["response"]
                
    return response_text
