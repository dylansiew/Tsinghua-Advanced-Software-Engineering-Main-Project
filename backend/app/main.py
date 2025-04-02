
from fastapi import FastAPI
from router.conversation import conversation_router
from router.test import test_router

server = FastAPI()
server.include_router(conversation_router)
# server.include_router(test_router)


@server.get("/")
async def root():
    return "Hello, this is a generic backend for a talking avatar."

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)

