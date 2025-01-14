import copy

import matplotlib.pyplot as plt
from Math.Geometry import interSectionCircleAndLine
from Math.distance import distance
from generatingData import generateTestData
from model.driver import driver
from model.order import Ds
from model.restaurant import restaurant
from pandas.core.frame import DataFrame
import itertools
import random

class RMDP:
    def __init__(self, delay: int, maxLengthPost: int, maxTimePost: int,
                 capacity: int, velocity: int, restaurantPrepareTime: int):

        self.Ds_0, self.D_x, self.D_y = generateTestData.importOrderValue()
        self.vehiceList, self.vehiclelist_x, self.vehiclelist_y = generateTestData.importVehicleValue()
        self.restaurantList, self.restauranList_x, self.restauranList_y = generateTestData.importRestaurantValue()
        self.x = 0
        self.D_0 = []  # Order
        self.Order_num = 2
        self.horizon = 1000
        self.vertical = 1000  # related plan
        self.Theta_x = [{"driverId": driver.get_id(), "route": []} for driver in self.vehiceList]
        self.Delta_S = 0
        self.P_x = []
        self.time_buffer = 0
        self.t_Pmax = 40
        self.distanceEpsilon = 10
        self.t_ba = 10
        self.delay = delay
        self.maxLengthPost = maxLengthPost
        self.maxTimePost = maxTimePost
        self.capacity = capacity
        self.velocity = velocity
        self.restaurantPrepareTime = restaurantPrepareTime

        for currentDelay in self.vehiceList:
            currentDelay.setVelocity(40)

        for vehicle in self.vehiceList:
            vehicle.setVelocity(self.velocity)
            vehicle.setCurrentCapacity(0)

        for restaurant in self.restaurantList:
            restaurant.setPrepareTime(self.restaurantPrepareTime)

    def runRMDP(self, state: int, T: int):
        delay: float = float("inf")
        Order_num = 5
        T = Order_num * T
        slack = 0
        S = 0  # state(not sure)
        self.D_0.clear()
        for i in range(T, T + Order_num):
            self.D_0.append(self.Ds_0[i])

        # counter for n! type sequences
        unassignedOrderPermutation = list(itertools.permutations(self.D_0))
        for permutation in unassignedOrderPermutation:
            Theta_hat = copy.deepcopy(self.Theta_x)  # Candidate route plan
            P_hat = copy.deepcopy(self.P_x)

            for D in permutation:
                possibleDriver = self.possibleDriver()
                currentPairdDriver: driver = self.FindVehicle(D,possibleDriver)
                D.setDriverId(currentPairdDriver.get_id())
                currentPairdRestaurent: restaurant = copy.deepcopy(self.restaurantList[D.getRestaurantId() - 1])
                currentPairdRestaurent.setOrderId(D.getId())
                currentPairdDriver.setCurrentCapacity(currentPairdDriver.getCurrentCapacity() + 1)
                self.AssignOrder(Theta_hat, D, currentPairdDriver, currentPairdRestaurent)
                if self.Postponement(P_hat, D, self.maxLengthPost, self.t_Pmax):
                    if D not in P_hat:
                        P_hat.append(D)
                else:
                    while (D.t - P_hat[0].t) >= self.t_Pmax:
                        possibleDriver = self.possibleDriver()
                        PairdDriver: driver = self.FindVehicle(P_hat[0],possibleDriver)
                        P_hat[0].setDriverId(PairdDriver.get_id())
                        PairdDriver.setCurrentCapacity(PairdDriver.getCurrentCapacity() + 1)
                        PairedRestaurent = copy.deepcopy(self.restaurantList[P_hat[0].getRestaurantId() - 1])
                        PairedRestaurent.setOrderId(D.getId())

                        self.AssignOrder(Theta_hat, P_hat[0], PairdDriver, PairedRestaurent)

                        P_hat.pop(0)
                        if len(P_hat) == 0:
                            break

                    if len(P_hat) >= self.maxLengthPost:
                        for pospondedOrder in P_hat:
                            possibleDriver = self.possibleDriver()
                            PairdDriver: driver = self.FindVehicle(pospondedOrder,possibleDriver)
                            PairdDriver.setCurrentCapacity(PairdDriver.getCurrentCapacity() + 1)
                            pospondedOrder.setDriverId(PairdDriver.get_id())
                            PairedRestaurent = copy.deepcopy(self.restaurantList[pospondedOrder.getRestaurantId() - 1])
                            PairedRestaurent.setOrderId(pospondedOrder.getId())
                            self.AssignOrder(Theta_hat, pospondedOrder, PairdDriver, PairedRestaurent)
                        P_hat.clear()
                    P_hat.append(D)
            S = self.TotalDelay()
            if (S < delay) or ((S == delay) and (self.Slack() < slack)):
                slack = self.Slack()
                delay = S
                self.Theta_x = copy.deepcopy(Theta_hat)
                self.P_x = copy.deepcopy(P_hat)
        print(self.Theta_x)
        self.Remove()

    def possibleDriver(self):
        count = 0
        delay = []
        driver = []
        probillty = []
        for routePerVehicle in self.Theta_x:
            delay.append(self.deltaSDelay(routePerVehicle))
            driver.append(self.vehiceList[count])
            probillty.append(random.random())
            count = count + 1
        
        result = {
            "driver":driver,
            "delay":delay,
            "probility":probillty
        }
        data = DataFrame(result)
       
        data = data.sort_values(by=['delay', 'probility'],ascending=[True,False])
        
        return data['driver'].to_list()

    def deltaSDelay(self, route: list):
        delay: float = 0.0
        tripTime: float = 0.0
        for i in range(1, len(route['route']), 1):
            previousNode = route['route'][i - 1]
            currentNode = route['route'][i]
            currentDistance = distance(previousNode.getLatitude(), previousNode.getLongitude(),
                                       currentNode.getLatitude(), currentNode.getLongitude())
            tripTime += currentDistance / self.velocity
            if isinstance(currentNode, Ds):
                delay += max(0, (tripTime + self.time_buffer) - (
                        currentNode.getDeadLine() + currentNode.get_timeRequest()))
        return delay

    def AssignOrder(self, Theta_hat, D: Ds, V: driver, currentParedRestaurent: restaurant):
        currentRoute: list = next((route for route in Theta_hat if route.get("driverId") == V.get_id()), [])

        if not currentRoute['route']:
            currentRoute['route'].append(currentParedRestaurent)
            currentRoute['route'].append(D)

        else:
            first: int = 0
            second: int = 1
            minDelayTime = float('inf')
            for i in range(0, len(currentRoute), 1):  # control Restaurant
                for j in range(i + 1, len(currentRoute) + 2, 1):  # find all the possible positioins of new order
                    tempList = copy.deepcopy(currentRoute)
                    tempList["route"].insert(i, currentParedRestaurent)
                    tempList["route"].insert(j, D)
                    delayTime = self.deltaSDelay(tempList)

                    if minDelayTime > delayTime:
                        minDelayTime = delayTime
                        first = i
                        second = j

            currentRoute['route'].insert(first, currentParedRestaurent)
            currentRoute['route'].insert(second, D)

    # main function

    def Slack(self):
        totalSlack: int = 0
        for routePerVehicle in self.Theta_x:
            totalSlack += self.slackDelay(routePerVehicle)
        return totalSlack

    def showPosition(self):
        plt.scatter(self.x_R, self.y_R, c='red', s=25)
        plt.scatter(self.x_V, self.y_V, c='green', s=25)
        plt.show()

    def updateDriverLocation(self, time):
        hasOrderVehicle: list = [routePerVehicle for routePerVehicle in self.Theta_x if
                                 (routePerVehicle['route'] != [])]
        for route in hasOrderVehicle:
            currentDriver: driver = self.vehiceList[route.get("driverId") - 1]
            targetDestination = route['route'][0]
            travledDistance = currentDriver.getVelocity() * time
            estimatedDistance = distance(currentDriver.getLatitude(),
                                         currentDriver.getLongitude(),
                                         targetDestination.getLatitude(),
                                         targetDestination.getLongitude())
            if travledDistance > 0:

                if travledDistance >= estimatedDistance:
                    currentDriver.setLatitude(targetDestination.getLatitude())
                    currentDriver.setLongitude(targetDestination.getLongitude())
                    route['route'].pop(0)
                else:
                    updatedLon, updatedLat = interSectionCircleAndLine(currentDriver.getLongitude(),
                                                                       currentDriver.getLatitude(),
                                                                       travledDistance,
                                                                       currentDriver.getLongitude(),
                                                                       currentDriver.getLatitude(),
                                                                       targetDestination.getLongitude(),
                                                                       targetDestination.getLatitude())
                    currentDriver.setLatitude(updatedLon)
                    currentDriver.setLongitude(updatedLat)

    def tripTime(self, driv: driver, res: restaurant, order: Ds):
        return (distance(driv.x, driv.y, res.xPosition, res.yPosition) +
                distance(res.xPosition, res.yPosition, order.x, order.y)) / self.velocity

    def FindVehicle(self, Order: Ds,possibledriver):
        OrderRestaurant = self.restaurantList[Order.getRestaurantId() - 1]
        minTimeDriver = possibledriver[0]
        minTimeTolTal = float('inf')
        handleDriver = [driver for driver in possibledriver if driver.getCurrentCapacity() < self.capacity]
        for currentDriver in handleDriver:
            currenTripTime: float = self.tripTime(currentDriver, OrderRestaurant, Order)
            if currenTripTime < minTimeTolTal:
                minTimeDriver = copy.deepcopy(currentDriver)
                minTimeTolTal = currenTripTime
        return minTimeDriver

    def slackDelay(self, route):
        delay: int = 0
        tripTime: int = 0
        currentDriver = self.vehiceList[route["driverId"] - 1]
        currentRoute: list = copy.deepcopy(route['route'])
        currentRoute.append(currentDriver)
        for i in range(1, len(currentRoute), 1):
            currentDistance = distance(currentRoute[i - 1].getLatitude(), currentRoute[i - 1].getLongitude(),
                                       currentRoute[i].getLatitude(),
                                       currentRoute[i].getLongitude())
            tripTime += currentDistance / self.velocity
            if isinstance(currentRoute[i], Ds):
                delay += max(0, currentRoute[i].getDeadLine() -
                             tripTime - self.time_buffer)
        return delay

    def TotalDelay(self):
        totalSlack: int = 0
        for routePerVehicle in self.Theta_x:
            totalSlack += self.deltaSDelay(routePerVehicle)
        return totalSlack

    def Remove(self):
        for pospondedOrder in self.P_x:
            currentPairedDriver: driver = self.vehiceList[pospondedOrder.getDriverId() - 1]
            targetRoute: list = next(
                (route for route in self.Theta_x if route.get("driverId") == currentPairedDriver.get_id()), [])
            ans = [node for node in targetRoute['route'] if
                   ((isinstance(node, Ds) and node.getId() != pospondedOrder.getId()) or
                    (isinstance(node, restaurant) and node.getOrderId() != pospondedOrder.getId()))]
            targetRoute['route'] = copy.deepcopy(ans[:])

    def Postponement(self, P_hat, D, p_max, t_Pmax):
        # P_hat,D, p_max, t_Pmax have the description
        # if Theta_hat != D:  # I don't know how to get current route plan
        if len(P_hat) == 0:  # if postponement set is empty
            return True
        elif len(P_hat) < self.maxLengthPost:  # if number of postponement <= max of postponement
            # The time difference with the first order of P_hat and check whether <= max
            if D.t - P_hat[0].t < t_Pmax:
                # of poatponement time
                return True
            else:
                return False
        else:
            return False
