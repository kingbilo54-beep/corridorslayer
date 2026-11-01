"""CORRIDOR SLAYER | Cannon System: Visuals, Positions and Upgrades."""
from __future__ import annotations
import math

class Cannon:
    def __init__(self, index, total, ring_radius=100):
        self.index = index
        self.angle = (index / total) * math.tau
        self.ring_radius = ring_radius
        self.level = 1
        
        self.x = math.cos(self.angle) * ring_radius
        self.z = math.sin(self.angle) * ring_radius
        self.y = 12.0
        self.muzzle_offset = 15.0

    def get_muzzle_position(self):
        mx = self.x + math.cos(self.angle) * self.muzzle_offset
        mz = self.z + math.sin(self.angle) * self.muzzle_offset
        my = self.y + 6.0
        return (mx, my, mz)

    def get_visual_parts(self, metallic=0.6):
        parts = []
        parts.append(("box", (14, 6, 12), (self.x, self.y, self.z), self.angle, metallic))
        parts.append(("box", (10, 4, 8), (self.x, self.y + 3, self.z), self.angle, metallic + 0.1))
        parts.append(("cyl", 2.5, 10, (self.x, self.y + 6, self.z), self.angle, metallic + 0.2))
        parts.append(("cyl_emissive", 1.2, 2, (self.x, self.y + 11, self.z), self.angle, 1.0))
        
        if self.level >= 2:
            offset_x = math.cos(self.angle + math.pi/2) * 3
            offset_z = math.sin(self.angle + math.pi/2) * 3
            parts.append(("cyl", 1.8, 8, (self.x + offset_x, self.y + 6, self.z + offset_z), self.angle, metallic + 0.2))
            parts.append(("cyl_emissive", 1.0, 1.5, (self.x + offset_x, self.y + 10, self.z + offset_z), self.angle, 1.0))
        
        if self.level >= 3:
            offset_x = math.cos(self.angle - math.pi/2) * 3
            offset_z = math.sin(self.angle - math.pi/2) * 3
            parts.append(("cyl", 1.8, 8, (self.x + offset_x, self.y + 6, self.z + offset_z), self.angle, metallic + 0.2))
            parts.append(("cyl_emissive", 1.0, 1.5, (self.x + offset_x, self.y + 10, self.z + offset_z), self.angle, 1.0))
        
        if self.level >= 4:
            parts.append(("box", (18, 8, 16), (self.x, self.y - 2, self.z), self.angle, metallic + 0.1))
        
        if self.level >= 5:
            parts.append(("cyl", 3.5, 12, (self.x, self.y + 8, self.z), self.angle, metallic + 0.3))
            parts.append(("cyl_emissive", 1.5, 3, (self.x, self.y + 14, self.z), self.angle, 1.0))
        
        return parts

class CannonSystem:
    def __init__(self, count=8, ring_radius=100):
        self.cannons = [Cannon(i, count, ring_radius) for i in range(count)]
    
    def upgrade_all(self, level):
        for cannon in self.cannons:
            cannon.level = level
    
    def get_all_parts(self, metallic=0.6):
        all_parts = []
        for cannon in self.cannons:
            all_parts.extend(cannon.get_visual_parts(metallic))
        return all_parts
    
    def get_muzzle_position(self, index):
        if 0 <= index < len(self.cannons):
            return self.cannons[index].get_muzzle_position()
        return self.cannons[0].get_muzzle_position()