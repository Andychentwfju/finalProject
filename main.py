from RMDP import RMDP
from generatingData import generateTestData


def main():
    delay = float('inf')
    buffer: int = 1
    maxLengthPost: int = 3  # p_max
    maxTimePost: int = 20  # minutes     #t_pmax
    capacity: int = 3
    velocity: int = 20
    restaurantRepareTime: int = 10 * 60
    instance = RMDP(delay, maxLengthPost, maxTimePost, capacity, velocity, restaurantRepareTime)

    potentialOrders: list = generateTestData.importOrderValue()


    for time in range(0, 480,5):
        s: int = 0  # state
        currentTime = time
        # Input: State S, time t, route plan Θ, unassigned orders $o
        # , buffer b, maximal number of postonements pmax,
        # maximum time allowed for postponement tpmax)

        # instance.runRMDP(s, currentTime, routePlan, UnassignedOrder,
        #                  buffer, maxLengthPost, maxTimePost)
        instance.runRMDP(s, currentTime, 0)

        # every time new order coming we will call RMDP model
        # to generate Decision and update the Driver location
        # for next order coming

        instance.updateDriverLocation(currentTime)


main()
