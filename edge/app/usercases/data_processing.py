from app.entities.agent_data import AgentData
from app.entities.processed_agent_data import ProcessedAgentData

ACCEL_REST_Z = 16667        

BUMP_THRESHOLD    = 1000
POTHOLE_THRESHOLD = -3000

ROAD_STATE_NORMAL  = "normal"
ROAD_STATE_BUMP    = "bump"
ROAD_STATE_POTHOLE = "pothole"


def process_agent_data(agent_data: AgentData) -> ProcessedAgentData:
    z_value = agent_data.accelerometer.z

    deviation = z_value - ACCEL_REST_Z

    if deviation <= POTHOLE_THRESHOLD:
        road_state = ROAD_STATE_POTHOLE
    elif deviation >= BUMP_THRESHOLD:
        road_state = ROAD_STATE_BUMP
    else:
        road_state = ROAD_STATE_NORMAL

    return ProcessedAgentData(
        road_state=road_state,
        agent_data=agent_data
    )