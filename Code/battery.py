class Battery:
    capacity = 100
    charge = capacity

# This function is used for using battery discharge calculation
    def discharge(amount):
        if amount <= Battery.charge:
            Battery.charge -= amount
        else:
            Battery.charge = 0

# This function is calculated for battery charging amount and charge system.
    def charge_battery(amount):
        if amount <= Battery.capacity - Battery.charge:
            Battery.charge += amount
        else:
            Battery.charge = Battery.capacity


    def get_charge_level(self):
        return Battery.charge


    def get_capacity(self):
        return Battery.capacity


    def get_batt_info(self):
        return f"Battery Level: {Battery.charge/Battery.capacity * 100:.2f}%, Capacity: {Battery.capacity}mAh"


def GetBattLvl():
    # Here, we directly return the desired battery level as 12.5 volts.
    battLvl = '12.52'
    return battLvl

def GetLogs():
    logs = 'Nothing Alarms'
    return logs

def GetSignctrNum():
    SignctrNum = '80000136'
    return SignctrNum

def GetCallSchedule():
    CallSchedule = 'ENA,T1,T2,T3,T4,T5,T6'
    return CallSchedule




