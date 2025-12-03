#!/usr/bin/env python3
"""
Claude Bouncing Star Screensaver - Standalone Mac Version
Fullscreen animated Claude asterisk with googly eyes and API endpoints for manipulation.
Matches theater.js feature parity from hf_clean web demo.

Endpoints:
  POST /api/manipulate_star - Manipulate the star (shrink, spin_out, drill, corner_trap, color, opacity, googly_eyes)
  GET /health - Health check
  GET /api/status - Current star state
  POST /api/reset - Reset star to default state

Run: python claude_screensaver.py [--port PORT] [--windowed]
"""

import argparse
import io
import json
import logging
import math
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import pygame
import cairosvg
from flask import Flask, jsonify, request
from flask_cors import CORS

# Display Settings
STAR_BASE_SIZE = 240
DEFAULT_COLOR = "#c04015"  # Claude orange
SNARKY_COLOR = "#b8230e"   # Deeper red

# Animation Settings
TARGET_FPS = 60
FRAME_TIME = 1.0 / TARGET_FPS

# Physics constants (matching theater.js)
EYE_GRAVITY = 0.008
EYE_FRICTION = 0.96
SPIN_THRESHOLD = 2.0  # Rotation speed threshold for centrifugal force

# Claude SVG
CLAUDE_SVG_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<svg id="Layer_1" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1104.33 1080">
  <defs><style>.cls-1{fill:FILL_COLOR_PLACEHOLDER;fill-rule:evenodd;stroke-width:0px;}</style></defs>
  <path class="cls-1" d="m290.56,0c81.75.46,84.09,61.27,107.89,117.66,30.05,71.18,72.18,137.58,106.18,205.47,10.09,20.14,21.33,71.09,36.82,83.55l3.43-.85c16.5-16.85,5.12-57.54,9.42-85.26,5.71-35.52,11.42-71.05,17.13-106.57,9.42-69.87-12.17-188.73,60.8-195.24,101.64,2.86-26.39,304.8-14.56,353.82-1.05,1.06,9.19,18.29,19.69,26.43,49.18-12.79,67.76-83.55,83.06-127.03,29.77-39.15,57.83-78.33,92.48-112.54,62.64-78.69,144.9-29.88,106.18,63.95-47.66,53.76-86.78,114.27-131.01,170.51-55.81,95.17-118.49,112.58,23.97,73.32,61.22-17.12,133.51-15.67,191.81-39.21,49.14-6.7,106.58,25.9,47.95,70.76-13.98,1.7-26.82,3.05-41.96,5.11-12.63,4.9-24.32,12.41-37.68,15.35s-41.49,5.37-76.21,9.38c-42.94,9.77-61.54,18.31-85.63,23.02-19.81,3.87-77.62,6.73-86.48,18.76,14.78,13.57,33.84,11.88,59.08,15.35,47.09,7.39,118.33,5.75,166.12,11.94,36.42,4.71,64.74-2.09,88.2,12.79,15.52,9.84,49.33,21.35,39.39,54.57-6.27,20.94-44.55,35.1-75.35,28.99-15.29-3.03-35.06-13.64-47.95-17.05-54.26-6.88-110.68-15.42-160.12-34.96-10.86-4.41-79.06-18.69-82.2-10.23-6.07,16.32,39.32,42.52,47.95,51.16,50.93,50.9,108.88,95.26,158.41,147.5,12.88,13.59,66.91,51.22,34.25,77.59-32.02.18-49.84-26.75-69.36-40.92-57.19-41.54-133.79-110.08-183.24-159.43-4,1.42-2.85,1.99-6.85,3.41-4.93,20.95,118.75,174.1,131.87,206.33,11.59,28.47,19.41,73.37-15.41,81.85-34.43,8.38-48.28-26.65-59.94-43.48-35.66-51.46-74.37-103.99-109.6-156.88-33.98-75.56-60.52-101.17-61.65,5.97-7.26,52.15-12.32,120.12-19.69,168.81-2,26.71-4,53.43-5.99,80.14-3.51,9.02-34.81,30.08-49.66,25.58-41.57-13.35-29.92-90.13-13.70-125.33,2.28-19.89,4.56-39.79,6.85-59.68,4.28-13.07,8.56-26.15,12.84-39.22,5.15-24.24,6-53.05,11.99-75.03,5.64-20.69,21.58-83.25.86-86.96-16.15,11.47-21.49,34.91-33.39,51.16-21.82,29.77-49.13,58.89-71.07,88.67-24.87,28.79-143.72,224.51-178.96,143.24-7.12-25.21,47.55-80.62,59.94-96.35,41.18-52.3,78.94-103.95,119.02-157.73,11.12-14.92,49.77-42.17,53.09-59.68l-3.43-5.12c-24.19-5.3-44.57,25.75-63.36,34.10-42.47,18.89-76.18,54.51-114.74,76.73-28.5,16.42-56.11,28.97-81.35,48.6-96.97,61.75-149.24-14.44-38.53-65.64,21.79-16.35,44.68-34.88,68.5-49.45,19.9-12.18,40.46-16.43,59.94-28.99,16.36-10.54,38.24-25.49,56.51-33.25,21.29-9.04,83.12-34.99,71.93-53.71-11.19-18.72-72.04-3.45-107.03-7.67-77.26-9.32-154.96-1.62-223.49-12.79-38.06-6.2-103.93,8.54-93.33-45.19,7.06-35.78,82.33-9.52,113.88-11.94,21.74-1.67,38.34,4.10,56.51,6.82,58.26,5.54,107.77,5.82,164.40,7.67,24.52,3.31,61.72,17.51,82.2,8.53,9.7-26.43-65.76-61.85-85.63-73.32-63.41-36.63-123.31-87.18-183.24-127.89-15.26-10.37-45.77-21.74-55.66-35.81-12.05-17.14-16.10-54.06-5.14-71.62,28.63-41.92,89.46.98,113.88,23.87,35.05,24.15,71.65,46.75,101.04,78.44,16.08,11.54,33.83,18.26,48.81,30.69,11.05,9.17,48.45,49.86,60.8,44.33,7.74-25.08-21.9-52.81-29.97-72.47-28.94-70.56-69.10-126.28-104.47-191.83-31.94-44.8-54.79-97.69,11.99-135.56Z"/>
</svg>
"""

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class EyeState:
    """State for a single googly eye"""
    angle: float = math.pi / 2  # Pupil angle (radians, 0=right, PI/2=down)
    velocity: float = 0.0       # Angular velocity


@dataclass
class StarState:
    """Current state of the star animation"""
    # Position and movement
    x: float = 0
    y: float = 0
    vx: float = 0.5  # Matching theater.js velocity
    vy: float = 0.5

    # Visual state
    current_scale: float = 1.0
    target_scale: float = 1.0
    rotation_angle: float = 0.0
    rotation_speed: float = 0.5  # degrees per frame (matching theater.js)
    color: str = DEFAULT_COLOR
    opacity: float = 1.0

    # Heartbeat pulse (QRS cardiac cycle)
    heartbeat_pulse: float = 0.0

    # Wall impact tracking
    wall_impact: float = 0.0

    # Googly eyes
    eyes_enabled: bool = False
    left_eye: EyeState = field(default_factory=EyeState)
    right_eye: EyeState = field(default_factory=EyeState)

    # Effect state tracking
    effect_active: str = None
    effect_start_time: float = 0.0

    # Spin out state (ramp + decay phases)
    spin_out_phase: str = None  # "ramp" or "decay"
    spin_out_ramp_start: float = 0.0

    # Corner trap state
    corner_trapped: bool = False
    trap_corner_x: float = 0
    trap_corner_y: float = 0
    saved_vx: float = 0
    saved_vy: float = 0

    # Shrink state
    shrink_end_time: float = 0.0

    # Color/opacity restore times
    color_end_time: float = 0.0
    opacity_end_time: float = 0.0

    # Drill state
    drill_end_time: float = 0.0
    drill_saved_vx: float = 0
    drill_saved_vy: float = 0


class ClaudeScreensaver:
    """Manages the bouncing Claude star animation with googly eyes"""

    def __init__(self, fullscreen: bool = True):
        self.fullscreen = fullscreen
        self.running = True
        self.screen = None
        self.display_width = 0
        self.display_height = 0
        self.state = StarState()
        self.master_sprites: Dict[str, pygame.Surface] = {}
        self.current_color = DEFAULT_COLOR
        self.lock = threading.Lock()
        self.default_rotation_speed = 0.5

    def initialize(self):
        """Initialize pygame and render sprites"""
        pygame.init()

        display_info = pygame.display.Info()

        if self.fullscreen:
            self.display_width = display_info.current_w
            self.display_height = display_info.current_h
            self.screen = pygame.display.set_mode(
                (self.display_width, self.display_height),
                pygame.FULLSCREEN | pygame.NOFRAME
            )
        else:
            self.display_width = 1280
            self.display_height = 720
            self.screen = pygame.display.set_mode(
                (self.display_width, self.display_height),
                pygame.NOFRAME
            )

        pygame.display.set_caption("Claude Screensaver")
        pygame.mouse.set_visible(False)

        # Initialize position to center
        self.state.x = self.display_width / 2
        self.state.y = self.display_height / 2

        # Render initial sprites
        self._render_sprite(DEFAULT_COLOR, "default")
        self._render_sprite(SNARKY_COLOR, "snarky")

        logger.info(f"Initialized at {self.display_width}x{self.display_height} (fullscreen={self.fullscreen})")

    def _render_sprite(self, color: str, key: str):
        """Render SVG sprite at given color"""
        svg_data = CLAUDE_SVG_XML.strip().replace("FILL_COLOR_PLACEHOLDER", color)
        png_data = cairosvg.svg2png(
            bytestring=svg_data.encode('utf-8'),
            output_width=STAR_BASE_SIZE * 2
        )
        image_bytes = io.BytesIO(png_data)
        self.master_sprites[key] = pygame.image.load(image_bytes).convert_alpha()

    def _render_custom_color(self, color: str):
        """Render sprite with custom color"""
        if color != self.current_color:
            self._render_sprite(color, "custom")
            self.current_color = color

    def get_current_sprite(self) -> pygame.Surface:
        """Get the current sprite based on state"""
        if self.state.color == DEFAULT_COLOR:
            return self.master_sprites.get("default")
        elif self.state.color == SNARKY_COLOR:
            return self.master_sprites.get("snarky")
        else:
            if "custom" not in self.master_sprites or self.current_color != self.state.color:
                self._render_custom_color(self.state.color)
            return self.master_sprites.get("custom", self.master_sprites["default"])

    def _cancel_spin_out(self):
        """Cancel any active spin_out effect"""
        if self.state.spin_out_phase:
            self.state.spin_out_phase = None
            self.state.rotation_speed = self.default_rotation_speed

    def _cancel_drill(self):
        """Cancel any active drill effect"""
        if self.state.drill_end_time > time.time():
            self.state.drill_end_time = 0
            self.state.vx = self.state.drill_saved_vx
            self.state.vy = self.state.drill_saved_vy
            self.state.rotation_speed = self.default_rotation_speed

    def manipulate(self, action: str, parameters: dict = None):
        """Apply manipulation to the star"""
        parameters = parameters or {}
        current_time = time.time()

        with self.lock:
            if action == "shrink":
                # Shrink to 20% for 15 seconds (matching theater.js)
                self.state.target_scale = 0.2
                self.state.shrink_end_time = current_time + 15.0
                self.state.effect_active = "shrink"
                logger.info("Shrinking star for 15 seconds")

            elif action == "spin_out":
                # Cancel conflicting drill effect
                self._cancel_drill()
                # Cancel existing spin_out
                self._cancel_spin_out()

                # Start fresh spin_out: ramp from 1 to ~11 over 2 seconds
                self.state.rotation_speed = 1.0
                self.state.spin_out_phase = "ramp"
                self.state.spin_out_ramp_start = current_time
                self.state.effect_active = "spin_out"
                logger.info("Starting spin out (ramp phase)")

            elif action == "drill":
                # Cancel conflicting spin_out effect
                self._cancel_spin_out()

                # Save velocity and stop movement
                self.state.drill_saved_vx = self.state.vx
                self.state.drill_saved_vy = self.state.vy
                self.state.vx = 0
                self.state.vy = 0
                self.state.rotation_speed = 10.0  # Fast spin (matching theater.js)
                self.state.drill_end_time = current_time + 3.0
                self.state.effect_active = "drill"
                logger.info("Starting drill for 3 seconds")

            elif action == "corner_trap":
                # Find nearest corner (50px padding matching theater.js)
                corners = [
                    (50, 50),
                    (self.display_width - 50, 50),
                    (50, self.display_height - 50),
                    (self.display_width - 50, self.display_height - 50)
                ]

                min_dist = float('inf')
                nearest = corners[0]
                for cx, cy in corners:
                    dist = math.sqrt((self.state.x - cx)**2 + (self.state.y - cy)**2)
                    if dist < min_dist:
                        min_dist = dist
                        nearest = (cx, cy)

                # Save velocity and trap
                self.state.saved_vx = self.state.vx
                self.state.saved_vy = self.state.vy
                self.state.vx = 0
                self.state.vy = 0
                self.state.corner_trapped = True
                self.state.trap_corner_x, self.state.trap_corner_y = nearest
                self.state.effect_active = "corner_trap"
                self.state.effect_start_time = current_time
                logger.info(f"Trapped in corner at ({nearest[0]}, {nearest[1]}) for 10 seconds")

            elif action == "color":
                color = parameters.get("color", DEFAULT_COLOR)
                if not color.startswith("#"):
                    color = f"#{color}"
                self.state.color = color
                self.state.color_end_time = current_time + 15.0
                logger.info(f"Changed color to {color} for 15 seconds")

            elif action == "opacity":
                opacity = parameters.get("opacity", 1.0)
                self.state.opacity = max(0.0, min(1.0, float(opacity)))
                self.state.opacity_end_time = current_time + 15.0
                logger.info(f"Changed opacity to {self.state.opacity} for 15 seconds")

            elif action == "googly_eyes":
                enabled = parameters.get("enabled", True)
                self.state.eyes_enabled = bool(enabled)
                logger.info(f"Googly eyes: {'enabled' if self.state.eyes_enabled else 'disabled'}")

            elif action == "reset":
                self._reset_state()
                logger.info("Reset to default state")

    def _reset_state(self):
        """Reset star to default state"""
        self.state.target_scale = 1.0
        self.state.current_scale = 1.0
        self.state.rotation_speed = self.default_rotation_speed
        self.state.color = DEFAULT_COLOR
        self.state.opacity = 1.0
        self.state.effect_active = None
        self.state.corner_trapped = False
        self.state.spin_out_phase = None
        self.state.shrink_end_time = 0
        self.state.color_end_time = 0
        self.state.opacity_end_time = 0
        self.state.drill_end_time = 0
        self.state.vx = 0.5
        self.state.vy = 0.5
        self.state.eyes_enabled = False
        self.state.left_eye = EyeState()
        self.state.right_eye = EyeState()

    def _update_heartbeat(self):
        """Update QRS cardiac cycle heartbeat pulse"""
        current_time = time.time()
        cycle_duration = 4.0
        phase = (current_time % cycle_duration) / cycle_duration

        heartbeat_pulse = 0.0
        if phase < 0.125:
            # Main QRS beat
            qrs_phase = phase / 0.125
            heartbeat_pulse = math.sin(qrs_phase * math.pi)
        elif phase < 0.2:
            # T-wave echo
            t_phase = (phase - 0.125) / 0.075
            heartbeat_pulse = math.sin(t_phase * math.pi) * 0.25

        self.state.heartbeat_pulse = heartbeat_pulse

    def _update_eye_physics(self):
        """Update googly eye physics"""
        if not self.state.eyes_enabled:
            return

        star_rot_rad = math.radians(self.state.rotation_angle)

        # Where "down" is from the eye's local point of view
        local_gravity_target = (math.pi / 2) - star_rot_rad

        # Centrifugal force only when spinning fast
        centrifugal_force = 0.0
        if abs(self.state.rotation_speed) > SPIN_THRESHOLD:
            centrifugal_force = abs(self.state.rotation_speed) * 0.05

        # Local outward targets for centrifugal force
        left_outward_target = math.pi   # "Left" from inside the eye
        right_outward_target = 0.0      # "Right" from inside the eye

        # Heartbeat reaction (subtle upward nudge)
        heartbeat_kick = self.state.heartbeat_pulse * 0.0069

        # Wall impact reaction
        impact_kick = self.state.wall_impact

        # Update left eye
        left_gravity_diff = local_gravity_target - self.state.left_eye.angle
        while left_gravity_diff > math.pi:
            left_gravity_diff -= math.pi * 2
        while left_gravity_diff < -math.pi:
            left_gravity_diff += math.pi * 2

        left_centrifugal_diff = left_outward_target - self.state.left_eye.angle
        while left_centrifugal_diff > math.pi:
            left_centrifugal_diff -= math.pi * 2
        while left_centrifugal_diff < -math.pi:
            left_centrifugal_diff += math.pi * 2

        self.state.left_eye.velocity += (left_gravity_diff * EYE_GRAVITY) + (left_centrifugal_diff * centrifugal_force)
        self.state.left_eye.velocity -= heartbeat_kick
        self.state.left_eye.velocity -= impact_kick
        self.state.left_eye.velocity *= EYE_FRICTION
        self.state.left_eye.angle += self.state.left_eye.velocity

        # Update right eye
        right_gravity_diff = local_gravity_target - self.state.right_eye.angle
        while right_gravity_diff > math.pi:
            right_gravity_diff -= math.pi * 2
        while right_gravity_diff < -math.pi:
            right_gravity_diff += math.pi * 2

        right_centrifugal_diff = right_outward_target - self.state.right_eye.angle
        while right_centrifugal_diff > math.pi:
            right_centrifugal_diff -= math.pi * 2
        while right_centrifugal_diff < -math.pi:
            right_centrifugal_diff += math.pi * 2

        self.state.right_eye.velocity += (right_gravity_diff * EYE_GRAVITY) + (right_centrifugal_diff * centrifugal_force)
        self.state.right_eye.velocity -= heartbeat_kick
        self.state.right_eye.velocity -= impact_kick
        self.state.right_eye.velocity *= EYE_FRICTION
        self.state.right_eye.angle += self.state.right_eye.velocity

    def _update_effects(self):
        """Update time-based effects"""
        current_time = time.time()

        # Decay wall impact
        self.state.wall_impact *= 0.85

        # Check shrink expiration
        if self.state.shrink_end_time > 0 and current_time >= self.state.shrink_end_time:
            self.state.shrink_end_time = 0
            self.state.target_scale = 1.0
            if self.state.effect_active == "shrink":
                self.state.effect_active = None

        # Check color expiration
        if self.state.color_end_time > 0 and current_time >= self.state.color_end_time:
            self.state.color_end_time = 0
            self.state.color = DEFAULT_COLOR

        # Check opacity expiration
        if self.state.opacity_end_time > 0 and current_time >= self.state.opacity_end_time:
            self.state.opacity_end_time = 0
            self.state.opacity = 1.0

        # Check drill expiration
        if self.state.drill_end_time > 0 and current_time >= self.state.drill_end_time:
            self.state.vx = self.state.drill_saved_vx
            self.state.vy = self.state.drill_saved_vy
            self.state.rotation_speed = self.default_rotation_speed
            self.state.drill_end_time = 0
            if self.state.effect_active == "drill":
                self.state.effect_active = None

        # Check corner trap expiration (10 seconds)
        if self.state.corner_trapped:
            if current_time - self.state.effect_start_time >= 10.0:
                self.state.corner_trapped = False
                self.state.vx = self.state.saved_vx
                self.state.vy = self.state.saved_vy
                if self.state.effect_active == "corner_trap":
                    self.state.effect_active = None

        # Update spin_out phases
        if self.state.spin_out_phase == "ramp":
            elapsed = current_time - self.state.spin_out_ramp_start
            if elapsed < 2.0:
                # Ramp: +0.5 every 100ms = +5 per second
                self.state.rotation_speed = 1.0 + (elapsed * 5.0)
            else:
                # Switch to decay phase
                self.state.spin_out_phase = "decay"

        elif self.state.spin_out_phase == "decay":
            # Decay: multiply by 0.95 every 100ms (~60fps means multiply each frame)
            # At 60fps, 0.95^6 per 100ms = ~0.735 per 100ms
            self.state.rotation_speed *= 0.992  # Approx 0.95 per 100ms at 60fps
            if self.state.rotation_speed < 0.1:
                self.state.rotation_speed = self.default_rotation_speed
                self.state.spin_out_phase = None
                if self.state.effect_active == "spin_out":
                    self.state.effect_active = None

    def update(self):
        """Update animation frame"""
        with self.lock:
            # Update heartbeat
            self._update_heartbeat()

            # Update time-based effects
            self._update_effects()

            # Calculate scale (heartbeat pulse when not shrinking)
            if self.state.shrink_end_time == 0:
                # Idle scale with heartbeat: pulse up to 108%
                idle_scale = 1.0 + (self.state.heartbeat_pulse * 0.08)
                self.state.target_scale = idle_scale

            # Smooth scale transitions
            self.state.current_scale += (self.state.target_scale - self.state.current_scale) * 0.15

            # Update rotation
            self.state.rotation_angle += self.state.rotation_speed

            # Update position
            if self.state.corner_trapped:
                # Jitter around corner (±20 pixels)
                self.state.x = self.state.trap_corner_x + (random.random() - 0.5) * 40
                self.state.y = self.state.trap_corner_y + (random.random() - 0.5) * 40
            elif self.state.drill_end_time == 0:  # Not drilling (stationary during drill)
                self._update_bouncing_position()

            # Update eye physics
            self._update_eye_physics()

    def _update_bouncing_position(self):
        """Update position with DVD-style bouncing"""
        next_x = self.state.x + self.state.vx
        next_y = self.state.y + self.state.vy

        # Account for pulsed size in collision
        pulsed_size = STAR_BASE_SIZE * self.state.current_scale
        radius = pulsed_size / 2
        padding = 4

        hit_wall = False

        # Wall collisions
        if next_x - radius < padding:
            self.state.vx = abs(self.state.vx)
            next_x = radius + padding
            hit_wall = True
        elif next_x + radius > self.display_width - padding:
            self.state.vx = -abs(self.state.vx)
            next_x = self.display_width - padding - radius
            hit_wall = True

        if next_y - radius < padding:
            self.state.vy = abs(self.state.vy)
            next_y = radius + padding
            hit_wall = True
        elif next_y + radius > self.display_height - padding:
            self.state.vy = -abs(self.state.vy)
            next_y = self.display_height - padding - radius
            hit_wall = True

        # Trigger wall impact for eye reaction
        if hit_wall:
            self.state.wall_impact = 0.02

        self.state.x = next_x
        self.state.y = next_y

    def _draw_googly_eyes(self):
        """Draw googly eyes on the star"""
        if not self.state.eyes_enabled:
            return

        eye_size = STAR_BASE_SIZE * self.state.current_scale * 0.06
        pupil_size = eye_size * 0.5
        eye_spacing = eye_size * 2.5
        star_rot_rad = math.radians(self.state.rotation_angle)

        # Calculate world positions for eye sockets
        left_eye_x = self.state.x - (eye_spacing / 2) * math.cos(star_rot_rad)
        left_eye_y = self.state.y - (eye_spacing / 2) * math.sin(star_rot_rad)
        right_eye_x = self.state.x + (eye_spacing / 2) * math.cos(star_rot_rad)
        right_eye_y = self.state.y + (eye_spacing / 2) * math.sin(star_rot_rad)

        # Draw left eye
        # Drop shadow
        shadow_color = (0, 0, 0, int(0.4 * 255 * self.state.opacity))
        pygame.draw.circle(self.screen, shadow_color[:3],
                          (int(left_eye_x), int(left_eye_y + 3)), int(eye_size))

        # White fill
        white_alpha = int(255 * self.state.opacity)
        pygame.draw.circle(self.screen, (255, 255, 255),
                          (int(left_eye_x), int(left_eye_y)), int(eye_size))

        # Subtle outline
        pygame.draw.circle(self.screen, (51, 51, 51),
                          (int(left_eye_x), int(left_eye_y)), int(eye_size), 1)

        # Left pupil
        left_pupil_world_angle = self.state.left_eye.angle + star_rot_rad
        left_pupil_dist = eye_size - pupil_size - 2
        left_pupil_x = left_eye_x + math.cos(left_pupil_world_angle) * left_pupil_dist
        left_pupil_y = left_eye_y + math.sin(left_pupil_world_angle) * left_pupil_dist
        pygame.draw.circle(self.screen, (0, 0, 0),
                          (int(left_pupil_x), int(left_pupil_y)), int(pupil_size))

        # Draw right eye
        # Drop shadow
        pygame.draw.circle(self.screen, shadow_color[:3],
                          (int(right_eye_x), int(right_eye_y + 3)), int(eye_size))

        # White fill
        pygame.draw.circle(self.screen, (255, 255, 255),
                          (int(right_eye_x), int(right_eye_y)), int(eye_size))

        # Subtle outline
        pygame.draw.circle(self.screen, (51, 51, 51),
                          (int(right_eye_x), int(right_eye_y)), int(eye_size), 1)

        # Right pupil
        right_pupil_world_angle = self.state.right_eye.angle + star_rot_rad
        right_pupil_dist = eye_size - pupil_size - 2
        right_pupil_x = right_eye_x + math.cos(right_pupil_world_angle) * right_pupil_dist
        right_pupil_y = right_eye_y + math.sin(right_pupil_world_angle) * right_pupil_dist
        pygame.draw.circle(self.screen, (0, 0, 0),
                          (int(right_pupil_x), int(right_pupil_y)), int(pupil_size))

    def render(self):
        """Render current frame"""
        self.screen.fill((0, 0, 0))

        sprite = self.get_current_sprite()
        if sprite is None:
            return

        # Scale
        scaled_size = int(STAR_BASE_SIZE * self.state.current_scale)
        scaled_sprite = pygame.transform.smoothscale(sprite, (scaled_size, scaled_size))

        # Rotate
        rotated_sprite = pygame.transform.rotate(scaled_sprite, self.state.rotation_angle)

        # Apply opacity if not 1.0
        if self.state.opacity < 1.0:
            rotated_sprite.set_alpha(int(self.state.opacity * 255))

        # Position
        rect = rotated_sprite.get_rect(center=(int(self.state.x), int(self.state.y)))

        self.screen.blit(rotated_sprite, rect.topleft)

        # Draw googly eyes on top
        self._draw_googly_eyes()

        pygame.display.flip()

    def get_status(self) -> dict:
        """Get current state for API"""
        with self.lock:
            return {
                "position": {"x": self.state.x, "y": self.state.y},
                "velocity": {"vx": self.state.vx, "vy": self.state.vy},
                "scale": self.state.current_scale,
                "rotation": self.state.rotation_angle,
                "rotation_speed": self.state.rotation_speed,
                "color": self.state.color,
                "opacity": self.state.opacity,
                "effect_active": self.state.effect_active,
                "corner_trapped": self.state.corner_trapped,
                "eyes_enabled": self.state.eyes_enabled,
                "heartbeat_pulse": self.state.heartbeat_pulse,
                "wall_impact": self.state.wall_impact,
                "display_size": {"width": self.display_width, "height": self.display_height}
            }

    def run(self):
        """Main animation loop"""
        self.initialize()
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.running = False

            self.update()
            self.render()
            clock.tick(TARGET_FPS)

        pygame.quit()

    def stop(self):
        """Stop the screensaver"""
        self.running = False


# Global screensaver instance
screensaver: Optional[ClaudeScreensaver] = None

# Flask app for API
app = Flask(__name__)
CORS(app)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Claude Screensaver",
        "running": screensaver.running if screensaver else False
    })


@app.route('/api/status', methods=['GET'])
def api_status():
    if screensaver:
        return jsonify(screensaver.get_status())
    return jsonify({"error": "Screensaver not running"}), 503


@app.route('/api/manipulate_star', methods=['POST'])
def manipulate_star():
    """
    Manipulate the bouncing star.

    Actions:
    - shrink: Shrink star to 0.2x for 15 seconds
    - spin_out: Ramp rotation then decay (2s ramp + gradual slowdown)
    - drill: Stationary rapid spin for 3 seconds
    - corner_trap: Lock to nearest corner for 10 seconds with jitter
    - color: Change color for 15 seconds (param: color="#hexcode")
    - opacity: Change opacity for 15 seconds (param: opacity=0.0-1.0)
    - googly_eyes: Toggle googly eyes (param: enabled=true/false)
    - reset: Reset to default state
    """
    if not screensaver:
        return jsonify({"error": "Screensaver not running"}), 503

    data = request.get_json() or {}
    action = data.get("action")
    parameters = data.get("parameters", {})

    if not action:
        return jsonify({"error": "Missing action parameter"}), 400

    valid_actions = ["shrink", "spin_out", "drill", "corner_trap", "color", "opacity", "googly_eyes", "reset"]
    if action not in valid_actions:
        return jsonify({"error": f"Invalid action. Valid: {valid_actions}"}), 400

    screensaver.manipulate(action, parameters)
    return jsonify({"status": "ok", "action": action, "parameters": parameters})


@app.route('/api/reset', methods=['POST'])
def reset_star():
    """Reset star to default state"""
    if not screensaver:
        return jsonify({"error": "Screensaver not running"}), 503

    screensaver.manipulate("reset")
    return jsonify({"status": "ok", "action": "reset"})


def run_flask(port: int):
    """Run Flask in a thread"""
    app.run(host='0.0.0.0', port=port, threaded=True, use_reloader=False)


def main():
    global screensaver

    parser = argparse.ArgumentParser(description='Claude Bouncing Star Screensaver')
    parser.add_argument('--port', type=int, default=9099, help='API server port (default: 9099)')
    parser.add_argument('--windowed', action='store_true', help='Run in windowed mode instead of fullscreen')
    args = parser.parse_args()

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║       Claude Bouncing Star Screensaver (Full Version)     ║
╠═══════════════════════════════════════════════════════════╣
║  API Endpoints (port {args.port}):                             ║
║    GET  /health              - Health check               ║
║    GET  /api/status          - Current star state         ║
║    POST /api/manipulate_star - Manipulate the star        ║
║    POST /api/reset           - Reset to default           ║
║                                                           ║
║  Manipulation Actions:                                    ║
║    shrink       - Tiny star (15s)                         ║
║    spin_out     - Ramp up then decay rotation             ║
║    drill        - Stationary rapid spin (3s)              ║
║    corner_trap  - Lock to corner with jitter (10s)        ║
║    color        - Change color (15s, param: color)        ║
║    opacity      - Change opacity (15s, param: opacity)    ║
║    googly_eyes  - Toggle eyes (param: enabled=true/false) ║
║    reset        - Return to default state                 ║
║                                                           ║
║  Features:                                                ║
║    - QRS cardiac heartbeat pulse animation                ║
║    - Googly eyes with physics (gravity, spin, wall hits)  ║
║    - Effect conflict resolution                           ║
║    - DVD-style bouncing with wall collision tracking      ║
║                                                           ║
║  Press ESC or Q to quit                                   ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Create screensaver
    screensaver = ClaudeScreensaver(fullscreen=not args.windowed)

    # Start Flask server in background thread
    flask_thread = threading.Thread(target=run_flask, args=(args.port,), daemon=True)
    flask_thread.start()
    logger.info(f"API server started on port {args.port}")

    # Run screensaver (blocking)
    try:
        screensaver.run()
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        screensaver.stop()
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
