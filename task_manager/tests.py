import time
import functools


def timer(func):
    @functools.wraps(func)
    def wrap():
        start_time = time.time()
        res = func()
        end_time = time.time()
        print(end_time - start_time)
        return res

    return wrap


def impl_dec(func):
    @functools.wraps(func)
    def wrap():
        print("implement 2 decorator")
        res = func()
        return res

    return wrap


@impl_dec
@timer
def print_hello():
    time.sleep(3)
    print("hello")


# print_hello()


class Component:
    def activate(self):
        print("Base component activated")


class Sensor(Component):
    def activate(self):
        print("Sensor activated")
        super().activate()


class Controller(Component):
    def activate(self):
        print("Controller activated")
        super().activate()


class SmartDevice(Sensor, Controller):
    def activate(self):
        print("SmartDevice starting up")
        super().activate()
        print("SmartDevice ready")


# device = SmartDevice()
# device.activate()

# SmartDevice starting up
# Sensor activated
# Controller activated
# Base component activated
# SmartDevice ready

def test_func(input_data: list = []) -> list:
    input_data.append(2)

    return input_data


print(test_func())
print(test_func())
print(test_func())
print(test_func([3]))
print(test_func([4]))
print(test_func())