import random
from math import factorial

import matplotlib.pyplot as plt

from Math.Geometry import interSectionCircleAndLine
from Math.distance import distance
from assignOrder import AssignOrder
from findVehicle import FindVehicle
from generatingData import generateTestData
from model import order
from nextPermutation import nextPermutation
from postponement import Postponement
from remove import Remove


class RMDP:
    def __init__(self):
        self.x = 0
        self.slack = 0
        self.D_0 = []  # Order
        self.R = []  # restaurant
        self.Order_num = 2
        self.Vehicle_num = 10
        self.horizon = 1000
        self.vertical = 1000
        self.Theta = []  # related plan
        self.S = 0  # state(not sure)
        self.Delta_S = 0
        self.P_x = 0
        self.time_buffer = 0
        self.p_max = 3
        self.t_Pmax = 40
        self.distanceEpsilon = 10
        self.t_ba = 10

    def runRMDP(self, T, Theta, delay: float):

        # Orders
        # parameters initialization
        # print(R)

        Order_num = 5
        T = Order_num * T
        for i in range(T, T + Order_num):
            self.D_0.append(self.Ds_0[i])
        sequence = factorial(Order_num)  # counter for n! type sequences

        while sequence:
            nextPermutation(self.D_0)
            D_hat = self.D_0
            Theta_hat = self.Theta  # Candidate route plan
            P_hat = []  # Set of postponements
            for D in D_hat:
                currentPairdDriver = FindVehicle(Theta_hat, D, self.time_buffer, self.V, self.R)
                Theta_hat = AssignOrder(Theta_hat, D, currentPairdDriver, self.R)

                if Postponement(P_hat, D, self.p_max, self.t_Pmax):
                    if D not in P_hat:
                        P_hat.append(D)
                else:
                    while D.t - P_hat[0].t > self.t_Pmax:
                        pairedDriver = FindVehicle(Theta_hat, P_hat[0], self.time_buffer, self.V, self.R)
                        Theta_hat = AssignOrder(Theta_hat, D, pairedDriver, self.R)
                        P_hat.pop(0)
                    if len(P_hat) >= self.p_max:
                        for i in range(0, len(P_hat)):
                            pairedDriver = FindVehicle(Theta_hat, P_hat[i], self.time_buffer, self.V, self.R)
                            Theta_hat = AssignOrder(Theta_hat, D, pairedDriver, self.R)
                        P_hat.clear
                    P_hat.append(D)
                x_hat = [Theta_hat, P_hat]
            delay = self.Slack(self.S, Theta_hat)  # delay with no postponement
            # plan with postpnement
            Theta_hat_postpone = Remove(Theta_hat, P_hat)
            delay_postpone = self.Slack(self.S, Theta_hat_postpone, self.time_buffer, self.t_ba)  # delay with postponement
            if delay_postpone < delay:
                Theta_hat = Theta_hat_postpone
            else:
                P_hat = P_hat.pop()
            sequence -= 1
        self.Theta_x = Theta_hat
        self.P_x = P_hat
        # Theta_x = Remove(Theta_x, self.P_x)

    from Math.distance import distance

    # main function
    def Slack(self, S, Routes):
        Slacks: int = 0
        for routePerVehicle in Routes:
            for destination in routePerVehicle.get("route"):
                Slacks += max(0, destination.get("timeDeadline") + self.t_ba - self.time_buffer - destination.get("arriveTime"))
        return Slacks
        # For every route plan Θ̂, the function calculates
        # the sum of differences between arrival time aD and deadline over
        # all orders: max{0, (tD + ¯t)−(aD + b)}.

    def showPosition(self):
        plt.scatter(self.x_R, self.y_R, c='red', s=25)
        plt.scatter(self.x_V, self.y_V, c='green', s=25)
        plt.show()

    def generatingData(self):
        self.R, self.x_R, self.y_R = generateTestData.importRestaurantValue()
        self.V, self.x_V, self.y_V = generateTestData.importVehicleValue()
        self.Ds_0, self.D_x, self.D_y = generateTestData.importOrderValue()

        for vehicle in self.V:
            vehicle.setVelocity(10)

        for restaurant in self.R:
            restaurant.setPrepareTime(10 * 60)

    def updateDriverLocation(self, time):
        for route in self.Theta:
            currentDriver = self.D[route.get("driverid")]
            targetDestination = currentDriver.route[0]
            travledDistance = currentDriver.getVelocity * time
            updatedLocation = interSectionCircleAndLine(currentDriver.getLongitude,
                                                        currentDriver.getLatitude,
                                                        travledDistance, currentDriver.getLongitude,
                                                        currentDriver.getLatitude, targetDestination.getLongitude,
                                                        targetDestination.getLatitude)
            if distance(updatedLocation.y, updatedLocation.x, targetDestination.y, targetDestination.x):
                currentDriver.route.pop(0)
            currentDriver.setLongitude(updatedLocation.x)
            currentDriver.setLatitude(updatedLocation.y)
