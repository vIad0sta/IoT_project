import requests
from kivy.app import App
from kivy_garden.mapview import MapMarker, MapView
from kivy.clock import Clock
from lineMapLayer import LineMapLayer
from scipy.signal import find_peaks
import numpy as np
from collections import deque
import math

STORE_URL = "http://localhost:8000/processed_agent_data/"

UPDATE_INTERVAL   = 2.0
ACCEL_BUFFER_SIZE = 40
PAGE_LIMIT        = 20
ACCEL_REST_Z      = 16667
MAX_JUMP_KM       = 0.05

BUMP_HEIGHT        =  2000
BUMP_PROMINENCE    =  1500
BUMP_DISTANCE      =  10
BUMP_WIDTH         =  2

POTHOLE_HEIGHT     = -2000
POTHOLE_PROMINENCE =  1500
POTHOLE_DISTANCE   =  10
POTHOLE_WIDTH      =  2

TRAFFIC_LIGHT_ICONS = {
    "red":    "images/traffic_light_red.png",
    "yellow": "images/traffic_light_yellow.png",
    "green":  "images/traffic_light_green.png",
}

PARKING_ICON = "images/parking_free.png"


class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.car_marker  = None
        self.line_layer  = LineMapLayer()
        self.accel_buffer = []
        self.last_processed_id = 0
        self.next_offset = 0
        self.last_point  = None
        self.point_queue = deque()
        self._replay_running = False
        self.mapview = None

        self._parking_markers: dict[str, MapMarker] = {}
        self._traffic_light_markers: dict[str, MapMarker] = {}

    def build(self):
        self.mapview = MapView(zoom=15, lat=50.4501, lon=30.5234)
        return self.mapview

    def on_start(self):
        self.mapview.add_layer(self.line_layer, mode="scatter")
        self.car_marker = MapMarker(
            lat=self.mapview.lat,
            lon=self.mapview.lon,
            source="images/car.png",
        )
        self.mapview.add_marker(self.car_marker)
        Clock.schedule_interval(self.update, UPDATE_INTERVAL)

    
    def update(self, *args):
        self._update_agent_data()

   
    def _update_agent_data(self):
        try:
            response = requests.get(
                STORE_URL,
                params={"offset": self.next_offset, "limit": PAGE_LIMIT},
                timeout=3,
            )
            response.raise_for_status()
            page = response.json()
        except Exception as e:
            print(f"[MapViewApp] Failed to fetch agent data: {e}")
            return

        if not page:
            return

        self.next_offset += len(page)
        page.sort(key=lambda r: r.get("id", 0))

        for record in page:
            self.last_processed_id = record.get("id", self.last_processed_id)
            self.accel_buffer.append(record.get("z", ACCEL_REST_Z))

        if len(self.accel_buffer) >= ACCEL_BUFFER_SIZE:
            self.check_road_quality()
            self.accel_buffer.clear()

        for r in page:
            lat = r.get("latitude")
            lon = r.get("longitude")
            if lat is not None and lon is not None:
                self.point_queue.append({
                    "lat": lat,
                    "lon": lon,
                    "parking": r.get("parking"),
                    "traffic_light": r.get("traffic_light")
                })

        if self.point_queue and not self._replay_running:
            self._replay_running = True
            self._replay_next(0)

    def _bring_sensors_to_front(self):
        all_sensor_markers = list(self._parking_markers.values()) + \
                             list(self._traffic_light_markers.values())

        for marker in all_sensor_markers:
            self.mapview.remove_marker(marker)
            self.mapview.add_marker(marker)

    
    def _handle_parking(self, lat: float, lon: float, data: dict):
        if not data:
            return
            
        marker_key = f"{lat}_{lon}"
        empty_count = data.get("empty_count", 0)
        source = PARKING_ICON

        if marker_key in self._parking_markers:
            marker = self._parking_markers[marker_key]
            if marker.source != source:
                marker.source = source
                self.mapview.trigger_update(0)
                print(f"[Parking] Updated at ({lat}, {lon}) → {'free' if empty_count > 0 else 'full'}")
        else:
            marker = MapMarker(lat=lat, lon=lon, source=source)
            self.mapview.add_marker(marker)
            self._parking_markers[marker_key] = marker
            print(f"[Parking] Added at ({lat}, {lon}), free: {empty_count}")

    def _handle_traffic_light(self, lat: float, lon: float, data: dict):
        if not data:
            return
            
        marker_key = f"{lat}_{lon}"
        state = data.get("state", "red")
        source = TRAFFIC_LIGHT_ICONS.get(state, TRAFFIC_LIGHT_ICONS["red"])

        if marker_key in self._traffic_light_markers:
            marker = self._traffic_light_markers[marker_key]
            if marker.source != source:
                marker.source = source
                self.mapview.trigger_update(0)
                print(f"[TrafficLight] Updated at ({lat}, {lon}) → {state}")
        else:
            marker = MapMarker(lat=lat, lon=lon, source=source)
            self.mapview.add_marker(marker)
            self._traffic_light_markers[marker_key] = marker
            print(f"[TrafficLight] Added at ({lat}, {lon}), state: {state}")

    def _replay_next(self, dt):
        if not self.point_queue:
            self._replay_running = False
            return
        
        point_data = self.point_queue.popleft()
        self.update_car_marker(point_data)
        
        delay = UPDATE_INTERVAL / max(len(self.point_queue) + 1, 1)
        Clock.schedule_once(self._replay_next, delay)

    def check_road_quality(self):
        data       = np.array(self.accel_buffer, dtype=float)
        normalised = data - ACCEL_REST_Z

        bump_indices, _ = find_peaks(
            normalised,
            height=BUMP_HEIGHT, prominence=BUMP_PROMINENCE,
            distance=BUMP_DISTANCE, width=BUMP_WIDTH,
        )
        pothole_indices, _ = find_peaks(
            -normalised,
            height=-POTHOLE_HEIGHT, prominence=POTHOLE_PROMINENCE,
            distance=POTHOLE_DISTANCE, width=POTHOLE_WIDTH,
        )

        point = (self.car_marker.lat, self.car_marker.lon)

        if len(bump_indices) > 0:
            print(f"[RoadQuality] {len(bump_indices)} bump(s) at {point}")
            # Clock.schedule_once(lambda dt, p=point: self.set_bump_marker(p), 0)

        if len(pothole_indices) > 0:
            print(f"[RoadQuality] {len(pothole_indices)} pothole(s) at {point}")
            # Clock.schedule_once(lambda dt, p=point: self.set_pothole_marker(p), 0)

    @staticmethod
    def _haversine_km(p1, p2):
        lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
        lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 6371 * 2 * math.asin(math.sqrt(a))

    def update_car_marker(self, point_data):
        lat = point_data["lat"]
        lon = point_data["lon"]
        current_point = (lat, lon)

        if self.last_point is not None:
            if self._haversine_km(self.last_point, current_point) > MAX_JUMP_KM:
                self.line_layer = LineMapLayer()
                self.mapview.add_layer(self.line_layer, mode="scatter")
                
        self.last_point     = current_point
        self.car_marker.lat = lat
        self.car_marker.lon = lon
        self.line_layer.add_point(current_point)
        
        if point_data.get("parking"):
            self._handle_parking(lat, lon, point_data["parking"])
            
        if point_data.get("traffic_light"):
            self._handle_traffic_light(lat, lon, point_data["traffic_light"])

        self.mapview.trigger_update(0)

    def set_pothole_marker(self, point):
        lat, lon = point
        self.mapview.add_marker(MapMarker(lat=lat, lon=lon, source="images/pothole.png"))
        print(f"[Marker] Pothole at ({lat}, {lon})")
        self._bring_sensors_to_front()

    def set_bump_marker(self, point):
        lat, lon = point
        self.mapview.add_marker(MapMarker(lat=lat, lon=lon, source="images/bump.png"))
        print(f"[Marker] Bump at ({lat}, {lon})")
        self._bring_sensors_to_front()


if __name__ == "__main__":
    MapViewApp().run()