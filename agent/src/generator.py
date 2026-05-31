import csv
import random
from datetime import datetime, timedelta

def load_coordinates(filename: str, num_samples: int):
    coords = []
    try:
        with open(filename, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                coords.append((float(row['latitude']), float(row['longitude'])))
    except FileNotFoundError:
        print(f"Помилка: файл {filename} не знайдено.")
        return []

    if not coords:
        return []

    step = max(1, len(coords) // num_samples)
    return coords[::step][:num_samples]


def generate_parking_csv(filename: str, coordinates: list, updates_per_sensor: int = 1):
    base_time = datetime.now()

    with open(filename, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['sensor_id', 'timestamp', 'latitude', 'longitude'])
        
        for i, (lat, lon) in enumerate(coordinates):
            sensor_id = f"P-{i+1}"
            
            for update_idx in range(updates_per_sensor):
                record_time = base_time + timedelta(minutes=update_idx * 5)
                
                w.writerow([
                    sensor_id,
                    record_time.isoformat(),
                    lat,
                    lon
                ])


def generate_traffic_light_csv(filename: str, coordinates: list, updates_per_sensor: int = 50):
    states = ['red', 'green', 'yellow']
    base_time = datetime.now()

    with open(filename, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['sensor_id', 'timestamp', 'latitude', 'longitude', 'state', 'time_remaining'])
        
        for i, (lat, lon) in enumerate(coordinates):
            sensor_id = f"TL-{i+1}"
            
            start_state_idx = random.randint(0, 2)
            
            for update_idx in range(updates_per_sensor):
                record_time = base_time + timedelta(seconds=update_idx * 30)
                
                current_state = states[(start_state_idx + update_idx) % len(states)]
                
                time_remaining = random.randint(1, 30)
                
                w.writerow([
                    sensor_id,
                    record_time.isoformat(),
                    lat,
                    lon,
                    current_state,
                    time_remaining
                ])

if __name__ == '__main__':
    print("Зчитування координат з data/gps.csv...")
    all_coords = load_coordinates('data/gps.csv', 10)
    
    if len(all_coords) < 2:
        print("Недостатньо координат у data/gps.csv для генерації сенсорів.")
        exit(1)

    half_idx = len(all_coords) // 2
    parking_coords = all_coords[:half_idx]
    traffic_light_coords = all_coords[half_idx:]

    print(f"Вибрано унікальних парковок: {len(parking_coords)}")
    print(f"Вибрано унікальних світлофорів: {len(traffic_light_coords)}")

    print("Генерація даних...")
    generate_parking_csv('./data/parking.csv', parking_coords, updates_per_sensor=1)
    generate_traffic_light_csv('./data/traffic_light.csv', traffic_light_coords, updates_per_sensor=10)
    
    print("Синтетичні дані згенеровано успішно! (parking.csv та traffic_light.csv)")