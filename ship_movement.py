"""CORRIDOR SLAYER | Ship Idle Movement"""
import math

class ShipMovement:
    def __init__(self):
        self.time = 0.0
        
        # Bewegungsparameter
        self.float_amplitude = 4.0
        self.drift_amplitude = 2.0
        self.tilt_amplitude = 1.5
        
        # Bewegungsgeschwindigkeiten
        self.float_speed = 1.1
        self.drift_speed = 0.65
        self.tilt_speed = 0.8
        
        # Aktuelle Bewegungswerte
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.angle = 0.0

    def update(self, dt):
        self.time += dt
        self.offset_y = math.sin(self.time * self.float_speed) * self.float_amplitude
        self.offset_x = math.sin(self.time * self.drift_speed) * self.drift_amplitude
        self.angle = math.sin(self.time * self.tilt_speed) * self.tilt_amplitude

    def get_position(self, base_x, base_y):
        return (base_x + self.offset_x, base_y + self.offset_y)

    def get_angle(self):
        return self.angle
