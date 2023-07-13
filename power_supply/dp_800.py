#!/usr/bin/env python3
import time
from pyvisa import ResourceManager

class DP800:
    """
    Rigol DP800 command wrapper.
    """

    def __init__(self, resource):

        self.resource = resource

        self.measure_LUT = {"Current": "CURR", "Voltage": "VOLT", "Power": "POWE"}
        
        self.limits_channel_current = {"CH1": 5, "CH2": 2, "CH3": 2}
        
        self.limits_channel_voltage = {"CH1": 8, "CH2": 30, "CH3": -30}

    def __enter__(self):
        self.inst = ResourceManager().open_resource(self.resource)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.inst:
            self.inst.close()

    @classmethod
    def from_resource_id(cls, resource_id):
        resource_manager = ResourceManager()
        for resource in resource_manager.list_resources():
            if resource_id in resource:
                return cls(resource)
        raise ValueError(f"No valid resource found for ID: {resource_id}")

    @classmethod
    def auto_connect(cls):
        resource_manager = ResourceManager()
        relevant_resources = [resource for resource in resource_manager.list_resources() if "DP8" in resource]

        if len(relevant_resources) == 0:
            raise ValueError("No valid DP800 series resource found.")
        elif len(relevant_resources) > 1:
            raise ValueError(f"Multiple DP800 series resources found: {relevant_resources}. Choose one manually, and use the from_resource_id() method.")

        return cls(relevant_resources[0])

    def query_channel(self):
        query_result = self.instance.query(":INST?").partition("\n")
        return int(query_result[0][2])

    def select_channel(self, channel_id):
        if not isinstance(channel_id, int):
            raise ValueError("Invalid input type. Channel ID should be an integer.")
        elif channel_id < 1 or channel_id > 3:
            raise ValueError("Invalid channel ID. It should be in the range 1-3.")

        curr_channel = self.query_channel()
        if curr_channel != channel_id:
            command = f":INST:NSEL {channel_id}"
            self.instance.write(command)
            time.sleep(0.5)

    def enable_channel(self):
        id = self.query_channel()
        command = f":OUTP CH{id},ON"
        self.instance.write(command)
        time.sleep(0.5)

    def disable_channel(self):
        id = self.query_channel()
        command = f":OUTP CH{id},OFF"
        self.instance.write(command)
        time.sleep(0.5)

    def measure_value(self, value):
        id = self.query_channel()
        key = self.measure_LUT[value]
        command = f"MEAS:{key}? CH{id}"
        result_str = self.instance.query(command).partition("\n")
        return float(result_str[0])

    def reset(self):
        self.instance.write("*RST")

    def set_current(self, in_current):
        id = self.query_channel()
        LUT_id = f"CH{id}"
        
        if in_current > self.limits_channel_current[LUT_id]:
            self.instance.write(":CURR 5")
            raise ValueError("Current value exceeds the limit.")
        
        command = f":CURR {in_current}"
        self.instance.write(command)
        time.sleep(0.5)

    def set_voltage(self, in_voltage):
        id = self.query_channel()
        LUT_id = f"CH{id}"
        
        if id <= 2:
            if in_voltage > self.limits_channel_voltage[LUT_id]:
                raise ValueError("Voltage exceeds the limit for the channel.")
        elif in_voltage < self.limits_channel_voltage[LUT_id]:
            raise ValueError("Voltage is below the limit for the channel.")
                
        command = f":VOLT {in_voltage}"
        self.instance.write(command)
        time.sleep(0.5)

    def set_ovp(self, volt_ovp):
        command_val = f"VOLT:PROT {volt_ovp}"
        command_on = "VOLT:PROT:STAT ON"
        
        self.instance.write(command_val)
        time.sleep(0.5)
        self.instance.write(command_on)
        time.sleep(0.5)

    def set_ocp(self, curr_ocp):
        command_val = f"CURR:PROT {curr_ocp}"
        command_on = "CURR:PROT:STAT ON"
        
        self.instance.write(command_val)
        time.sleep(0.5)
        self.instance.write(command_on)
        time.sleep(0.5)

    def disable_op(self):
        command_off = "CURR:PROT:STAT OFF"
        self.instance.write(command_off)
        time.sleep(0.5)
        command_off = "VOLT:PROT:STAT OFF"
        self.instance.write(command_off)
