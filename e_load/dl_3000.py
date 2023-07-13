import time
from pyvisa import ResourceManager

class DL3000(object):
    """
    Rigol DL3000 command wrapper.
    """
    def __init__(self, inst):
        self.key_app_state = 0
        self.inst = inst

        # Key IDs
        self.key_utility = 9
        self.key_down_arrow = 40
        self.knob_cntclk_w = 35

    def __enter__(self):
        self.inst = ResourceManager().open_resource(self.resource_string)
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
        relevant_resources = [resource for resource in resource_manager.list_resources() if "DL3" in resource]

        if len(relevant_resources) == 0:
            raise ValueError("No valid DL3000 series resource found.")
        elif len(relevant_resources) > 1:
            raise ValueError(f"Multiple DL3000 series resources found: {relevant_resources}")
        
        return cls(relevant_resources[0])

    def get_voltage(self):
        return float(self.inst.query(":MEAS:VOLT?").partition("\n")[0])

    def get_current(self):
        return float(self.inst.query(":MEAS:CURR?").partition("\n")[0])

    def get_power(self):
        return float(self.inst.query(":MEAS:POW?").partition("\n")[0])

    def get_resistance(self):
        return float(self.inst.query(":MEAS:RES?").partition("\n")[0])

    def set_cc_slew_rate(self, slew):
        self.inst.write(f":SOURCE:CURRENT:SLEW {slew}")

    def is_enabled(self):
        return self.inst.query(":SOURCE:INPUT:STAT?").strip() == "1"

    def enable(self):
        self.inst.write(":SOURCE:INPUT:STAT ON")

    def disable(self):
        self.inst.write(":SOURCE:INPUT:STAT OFF")

    def set_mode(self, mode="CC"):
        self.inst.write(":SOURCE:FUNCTION {}".format(mode))

    def query_mode(self):
        return self.inst.query(":SOURCE:FUNCTION?").strip()

    def set_cc_current(self, current):
        '''set current in constant current mode'''
        return self.inst.write(":SOURCE:CURRENT:LEV:IMM {}".format(current))

    def set_cp_power(self, power):
        '''set power in constant power mode'''
        return self.inst.write(":SOURCE:POWER:LEV:IMM {}".format(power))

    def set_cp_i_lim(self, i_lim):
        '''set current limit in constant power mode'''
        return self.inst.query(":SOURCE:POWER:ILIM {}".format(i_lim))

    def set_cc(self, current, activate=True):
        ''' set constant current mode'''
        self.set_mode("CC")
        self.set_cc_current(current)
        if activate:
            self.enable()

    def set_cp(self, power, activate=True):
        ''' set constant power mode'''
        self.set_mode("CP")
        self.set_cp_power(power)
        if activate:
            self.enable()

    def reset(self):
        return self.inst.write("*RST")

    def set_voltage(self, voltage):
        return self.inst.write(":SOURCE:VOLTAGE:LEV:IMM {}".format(voltage))

    def sim_app_key(self):
        self.key_app_state = (self.key_app_state + 1) % 3
        return self.inst.write(":SYST:KEY 13")

    def sim_int_key_press(self, value):
        return self.inst.write(":SYST:KEY {}".format(20 + value))

    def sim_key_press(self, key_id):
        self.inst.write(":SYST:KEY {}".format(key_id))
        time.sleep(1)
        return
    
    def setup_sense(self):
        self.sim_key_press(self.key_utility)
        for _ in range(5):
            self.sim_key_press(self.key_down_arrow)
        self.sim_key_press(self.knob_cntclk_w)
        self.sim_key_press(self.key_utility)
        return

    def set_battery_discharge_current(self, in_current):
        '''For discharging a battery, set the discharge current'''
        if in_current >= 40:
            return False
        self.inst.write(":SYST:KEY 14")
        look_4_decimal_ptn = False
        max_entries = 5
        if isinstance(in_current, int):
            look_4_decimal_ptn = True
            if in_current > 9.999:
                max_entries = 6
        in_current_string = str(in_current)
        key_presses = min(max_entries, len(in_current_string))
        curr_integer = 0
        for i in range(0, key_presses):
            if look_4_decimal_ptn is True:
                if in_current_string[i] == '.':
                    look_4_decimal_ptn = False
                    self.inst.write(":SYST:KEY 30")
                    time.sleep(1)
                    continue
            curr_integer = int(in_current_string[i])
            self.sim_int_key_press(curr_integer)
            time.sleep(1)
        self.inst.write(":SYST:KEY 41")
        return True

    def set_batt_cutoff_voltage(self, in_voltage, cut_off):
        if in_voltage < cut_off:
            return False
        self.inst.write(":SYST:KEY 16")
        time.sleep(2)
        self.inst.write(":SYST:KEY 16")
        look_4_decimal_ptn = False
        max_entries = 5
        if isinstance(cut_off, int):
            look_4_decimal_ptn = True
            if cut_off > 9.999:
                max_entries = 6
        in_voltage_string = str(cut_off)
        key_presses = min(max_entries, len(in_voltage_string))
        curr_integer = 0
        for i in range(0, key_presses):
            if look_4_decimal_ptn is True:
                if in_voltage_string[i] == '.':
                    look_4_decimal_ptn = False
                    self.inst.write(":SYST:KEY 30")
                    time.sleep(1)
                    continue
            curr_integer = int(in_voltage_string[i])
            self.sim_int_key_press(curr_integer)
            time.sleep(1)
        self.inst.write(":SYST:KEY 41")
        return True