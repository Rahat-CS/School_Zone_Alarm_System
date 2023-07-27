from enum import Enum, auto

class Status_Display(Enum):
    ALARM = 0, "Alarm state", {0: "No alarms", 1: "Alarm Occurred"}
    DISPERR = 1, "Display error state", {0: "Normal", 1: "A fault has occurred in the displays"}
    CFGERR = 2, "Configuration error state", {0: "Normal", 1: "Configuration is corrupt (reset when rebooted)"}
    FWDL = 3, "Firmware Download", {0: "Normal", 1: "Firmware downloading"}
    FWDLER = 4, "Firmware Download Error", {0: "Normal", 1: "Error Occurred during Firmware Downloading"}
    BTTLW = 5, "Battery Low Voltage", {0: "Normal", 1: "Battery Voltage is below threshold"}
    FLH = 6, "Flashing State", {0: "One or more alert are flashing", 1: "No alert displays are flashing"}
    SOP = 7, "State of Operation", {0: "State of Operation Off", 1: "State of Operation On"}
    DOORSTS = 8, "Door Open State", {0: "Door is Closed", 1: "Door is Open"}

    def __str__(self):
        value_0 = self.value[0]
        name = self.name
        value_1 = self.value[1]
        additional_info = self.value[2].get(value_0, "Undefined")
        return f"{value_0}\t{name}\t{value_1}\t{additional_info}"

# Printing the details of each status display
for state in Status_Display:
    print(state)
