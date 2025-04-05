from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router.conversation import conversation_router
from router.test import test_router

server = FastAPI()

# Add CORS middleware
server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

server.include_router(conversation_router)
server.include_router(test_router)


@server.get("/")
async def root():
    return "Hello, this is a generic backend for a talking avatar."
