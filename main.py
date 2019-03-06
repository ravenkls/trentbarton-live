import trentbarton
from win10toast import ToastNotifier
import time

if __name__ == '__main__':
    toaster = ToastNotifier()

    stop = trentbarton.BusStop('Chain Lane', 262)
    live_times = stop.get_live_times()
    bus = live_times[0]

    toaster.show_toast(stop.name, f'{bus} is {bus.due} minutes away', icon_path=bus.icon, duration=7)
