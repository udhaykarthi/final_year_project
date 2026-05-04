"""
Singleton camera manager.

Problem this solves
-------------------
On Windows (DirectShow) only ONE process can hold a webcam open. The MJPEG
preview endpoint and the /analyze endpoint both used to call cv2.VideoCapture
independently, which caused random failures (black frames, timeouts, "vision
model disabled" because the snapshot was empty, etc.).

Solution
--------
Open the camera ONCE in a background thread and continuously read frames
into a small ring buffer. Both the MJPEG generator and the analyze endpoint
just grab the latest frame from memory — no more contention.
"""
from __future__ import annotations

import threading
import time
from typing import Optional

import cv2
import numpy as np


class CameraManager:
    """Process-wide singleton."""

    _instance: Optional["CameraManager"] = None
    _instance_lock = threading.Lock()

    @classmethod
    def get(cls, camera_index: int = 0) -> "CameraManager":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = CameraManager(camera_index)
                cls._instance.start()
            elif cls._instance.camera_index != camera_index:
                # Switch camera if needed
                cls._instance.stop()
                cls._instance = CameraManager(camera_index)
                cls._instance.start()
            return cls._instance

    # ------------------------------------------------------------------
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame: Optional[np.ndarray] = None
        self._frame_ts: float = 0.0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._opened = False

    # ------------------------------------------------------------------
    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name=f"CameraManager[{self.camera_index}]",
            daemon=True,
        )
        self._thread.start()
        # Give the thread a moment to actually open the camera
        for _ in range(50):
            if self._opened or self._stop.is_set():
                break
            time.sleep(0.05)

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self._opened = False

    # ------------------------------------------------------------------
    def _open(self) -> bool:
        # Try DirectShow first (best on Windows), fall back to default backend
        for backend in (cv2.CAP_DSHOW, cv2.CAP_ANY):
            cap = cv2.VideoCapture(self.camera_index, backend)
            if cap.isOpened():
                self._cap = cap
                self._opened = True
                return True
            cap.release()
        return False

    def _run(self):
        if not self._open():
            print(f"[CameraManager] FAILED to open camera {self.camera_index}")
            return
        print(f"[CameraManager] Camera {self.camera_index} opened.")

        empty_reads = 0
        while not self._stop.is_set():
            ok, frame = self._cap.read()
            if not ok or frame is None:
                empty_reads += 1
                if empty_reads > 30:
                    # Try to reopen
                    print("[CameraManager] Too many empty reads, reopening...")
                    self._cap.release()
                    self._opened = False
                    if not self._open():
                        time.sleep(0.5)
                        continue
                    empty_reads = 0
                time.sleep(0.02)
                continue

            empty_reads = 0
            with self._lock:
                self._frame = frame
                self._frame_ts = time.time()
            # ~30 fps cap
            time.sleep(0.03)

        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._opened = False
        print("[CameraManager] Stopped.")

    # ------------------------------------------------------------------
    def get_frame(self, timeout: float = 2.0) -> Optional[np.ndarray]:
        """Return a copy of the most recent frame, or None if unavailable."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if self._frame is not None:
                    return self._frame.copy()
            time.sleep(0.05)
        return None

    def get_jpeg(self, quality: int = 70) -> Optional[bytes]:
        frame = self.get_frame(timeout=0.5)
        if frame is None:
            return None
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not ok:
            return None
        return buf.tobytes()

    def is_alive(self) -> bool:
        return self._opened and self._thread is not None and self._thread.is_alive()

