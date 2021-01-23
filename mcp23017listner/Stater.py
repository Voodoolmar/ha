import time

DEBOUNCE_TIME = 0.02
MULTI_CLICK_TIME = 0.25
LONG_CLICK_TIME = 1.0

class Stater:
    def __init__(
            self,
            pin,
            callback
    ):
        """Initialize the entity."""
        self.pin = pin
        self.clickCount = 0
        self.lastBounceTime = time.time()
        self.lastState = False
        self.pressed = False
        self.long = False
        self.callback = callback

    def update(self, btnState):
        now = time.time()
        if btnState != self.lastState:
            self.lastBounceTime = now

        t = now - self.lastBounceTime;

        if (t > DEBOUNCE_TIME) & (btnState != self.pressed):
            self.pressed = btnState
            if self.pressed:
                self.clickCount += 1

        if (not self.pressed) & (t > MULTI_CLICK_TIME):
            if self.clickCount == 1:
                self.callback({"action": "single"})
            elif self.clickCount == 2:
                self.callback({"action": "double"})
            elif self.clickCount == 3:
                self.callback({"action": "triple"})
            self.clickCount = 0;

        if self.pressed & (t > LONG_CLICK_TIME):
            self.long = True

        if (not self.pressed) & self.long:
            self.callback({"action": "long"})
            self.clickCount = 0
            self.long = False

        self.lastState = btnState