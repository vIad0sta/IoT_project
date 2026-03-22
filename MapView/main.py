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
UPDATE_INTERVAL = 2.0
ACCEL_BUFFER_SIZE = 40  
PAGE_LIMIT = 20        
ACCEL_REST_Z = 16667
MAX_JUMP_KM = 0.05 

BUMP_HEIGHT      =  2000   
BUMP_PROMINENCE  =  1500
BUMP_DISTANCE    =  10
BUMP_WIDTH       =  2
 
POTHOLE_HEIGHT      = -2000
POTHOLE_PROMINENCE  =  1500
POTHOLE_DISTANCE    =  10
POTHOLE_WIDTH       =  2
 
 
class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
 
        self.car_marker = None
 
        self.line_layer = LineMapLayer()
 
        self.accel_buffer = []
 
        self.last_processed_id = 0
 
        self.next_offset = 0
        
        self.last_point = None

        self.point_queue = deque()
        self._replay_running = False
 
        self.mapview = None
 
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
        new_records = []
        offset = self.next_offset
 
        try:
            response = requests.get(
                STORE_URL,
                params={"offset": offset, "limit": PAGE_LIMIT},
                timeout=3,
            )
            response.raise_for_status()
            page = response.json()

        except Exception as e:
            print(f"[MapViewApp] Failed to fetch data from Store: {e}")
            return
        
        new_records.extend(page)
        offset += len(page)

        self.next_offset = offset
 
        if not new_records:
            return
 
        new_records.sort(key=lambda r: r.get("id", 0))
 
        for record in new_records:
            self.last_processed_id = record.get("id", self.last_processed_id)
            self.accel_buffer.append(record.get("z", ACCEL_REST_Z))
 
        if len(self.accel_buffer) >= ACCEL_BUFFER_SIZE:
            self.check_road_quality()
            self.accel_buffer.clear()
 
        for r in new_records:
            if r.get("latitude") is not None and r.get("longitude") is not None:
                self.point_queue.append((r.get("latitude"), r.get("longitude")))
 
        if self.point_queue and not self._replay_running:
            self._replay_running = True
            self._replay_next(0)

    def _replay_next(self, dt):
        if not self.point_queue:
            self._replay_running = False
            return
 
        point = self.point_queue.popleft()
        self.update_car_marker(point)
 
        delay = UPDATE_INTERVAL / max(len(self.point_queue) + 1, 1)
        Clock.schedule_once(self._replay_next, delay)

    def check_road_quality(self):
        data = np.array(self.accel_buffer, dtype=float)
 
        normalised = data - ACCEL_REST_Z
 
        bump_indices, _ = find_peaks(
            normalised,
            height=BUMP_HEIGHT,
            prominence=BUMP_PROMINENCE,
            distance=BUMP_DISTANCE,
            width=BUMP_WIDTH,
        )
 
        pothole_indices, _ = find_peaks(
            -normalised,
            height=-POTHOLE_HEIGHT,
            prominence=POTHOLE_PROMINENCE,
            distance=POTHOLE_DISTANCE,
            width=POTHOLE_WIDTH,
        )
 
        current_lat = self.car_marker.lat
        current_lon = self.car_marker.lon
        point = (current_lat, current_lon)
 
        if len(bump_indices) > 0:
            print(f"[RoadQuality] {len(bump_indices)} bump(s) detected at {point}")
            Clock.schedule_once(lambda dt, p=point: self.set_bump_marker(p), 0)
 
        if len(pothole_indices) > 0:
            print(f"[RoadQuality] {len(pothole_indices)} pothole(s) detected at {point}")
            Clock.schedule_once(lambda dt, p=point: self.set_pothole_marker(p), 0)
 
    @staticmethod
    def _haversine_km(p1, p2):
        lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
        lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 6371 * 2 * math.asin(math.sqrt(a))
    
    def update_car_marker(self, point):
        lat, lon = point
 
        if self.last_point is not None:
            dist = self._haversine_km(self.last_point, point)
            if dist > MAX_JUMP_KM:
                self.line_layer = LineMapLayer()
                self.mapview.add_layer(self.line_layer, mode="scatter")
 
        self.last_point = point
 
        self.car_marker.lat = lat
        self.car_marker.lon = lon
 
        self.line_layer.add_point(point)
 
        self.mapview.trigger_update(0)
 
    def set_pothole_marker(self, point):
        lat, lon = point
        marker = MapMarker(
            lat=lat,
            lon=lon,
            source="images/pothole.png",
        )
        self.mapview.add_marker(marker)
        print(f"[Marker] Pothole placed at ({lat}, {lon})")
 
    def set_bump_marker(self, point):
        lat, lon = point
        marker = MapMarker(
            lat=lat,
            lon=lon,
            source="images/bump.png",  
        )
        self.mapview.add_marker(marker)
        print(f"[Marker] Bump placed at ({lat}, {lon})")
 
 
if __name__ == "__main__":
    MapViewApp().run()