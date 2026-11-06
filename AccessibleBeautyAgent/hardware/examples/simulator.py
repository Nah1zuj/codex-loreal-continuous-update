"""Run after installing local hardware package; no network or physical action."""
from trace_hardware.core import Simulator
if __name__=='__main__':
    device=Simulator();device.connect()
    print(device.display({'title':'TRACE SIMULATOR','instruction':'One step at a time'}))
    print(device.set_lighting(55,4200,consent=True))
    print(device.camera_state());device.disconnect();print(device.get_status())
