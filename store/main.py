from fastapi import FastAPI

from routers import parking, processed_agent_data, traffic_light
from websocket_manager import websocket_endpoint

app = FastAPI()

app.add_api_websocket_route("/ws/", websocket_endpoint)

app.include_router(processed_agent_data.router)
app.include_router(parking.router)
app.include_router(traffic_light.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)