from app.common.imports import *

class TangoServer(Device):

    # Vars
    STARTER = None

    @property
    def t(self):
        return self.s

    @property
    def s(self):
        return self.STARTER

    @s.setter
    def s(self, v):
        self.STARTER = v

    def debug(self, msg):
        if self.s is not None:
            self.s.debug(msg)
        self.debug_stream(msg)

    def error(self, msg):
        if self.s is not None:
            self.error(msg)
        self.error_stream(msg)

    def info(self, msg):
        if self.s is not None:
            self.s.info(msg)
        self.info_stream(msg)

    def warning(self, msg):
        if self.s is not None:
            self.s.warning(msg)
        self.warning_stream(msg)

    def _stateON(self):
        """
        Sets the state to predefined values
        :return:
        """
        self.set_state(DevState.ON)

    def _stateFAULT(self):
        """
        Sets the state to predefined values
        :return:
        """
        self.set_state(DevState.FAULT)

    def _stateUNKNOWN(self):
        """
        Sets the state to predefined values
        :return:
        """
        self.set_state(DevState.UNKNOWN)

    def _stateMOVING(self):
        """
        Sets the state to predefined values
        :return:
        """
        self.set_state(DevState.MOVING)

    def _stateRUNNING(self):
        """
        Sets the state to predefined values
        :return:
        """
        self.set_state(DevState.RUNNING)

    def _stateALARM(self):
        """
        Sets the state to predefined values
        :return:
        """
        self.set_state(DevState.ALARM)