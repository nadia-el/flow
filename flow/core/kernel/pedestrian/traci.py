from flow.core.kernel.pedestrian import KernelPedestrian
import traci.constants as tc
import numpy as np

class TraCIPedestrian(KernelPedestrian):

    def __init__(self,
            master_kernel):

        KernelPedestrian.__init__(self, master_kernel)

        # ids of all pedestrians in the simulation
        # (departed but yet to arrive)
        self.__ids = set()

        # sumo_observation variable that will carry all information on the
        # state of the pedestrians for a given timestep
        self.__sumo_obs = {}

    def update(self, reset):

        # subscribed variables of active pedestrians
        ped_obs = {}

        # pedestrians currently active in the simulation
        # cross-check with self.__ids to see which pedestrians
        # arrived and departed
        obs_ids = set(self.kernel_api.person.getIDList())

        # iterate through observed pedestrian and mark them as departed
        # if they have not been seen before (part of self.__ids)
        # NOTE: getIDList() method above seems to also return the ID of the
        # next pedestrian enterring the simulation so we need to check if the
        # pedestrian is valid (speed == 0), might not be the best method to check
        # as a pedestrian might have speed == 0 when waiting at an intersectionself.
        # Querying the position of a pedestrian in the simulation throws an error
        # TODO: fix the above note
        for ped_id in obs_ids:
            valid = self.kernel_api.person.getSpeed(ped_id) != 0
            if ped_id not in self.__ids and valid:
                obs = self._add_departed(ped_id)
                ped_obs[ped_id] = obs

        for ped_id in self.__ids.copy():
            if ped_id not in obs_ids:
                self.remove(ped_id)

        # Update subscribed attributes of pedestrians
        for ped_id in self.__ids:
            ped_obs[ped_id] = \
                    self.kernel_api.person.getSubscriptionResults(ped_id)
        self.__sumo_obs = ped_obs

    def _add_departed(self, ped_id):
        if ped_id not in self.__ids:
            self.__ids.add(ped_id)

        # subscribe new pedestrian
        self.kernel_api.person.subscribe(ped_id, [
            tc.VAR_POSITION, tc.VAR_SPEED, tc.VAR_ROAD_ID])

        # get initial state info
        self.__sumo_obs[ped_id] = dict()
        self.__sumo_obs[ped_id][tc.VAR_POSITION] = \
            self.kernel_api.person.getPosition(ped_id)
        self.__sumo_obs[ped_id][tc.VAR_SPEED] = \
            self.kernel_api.person.getSpeed(ped_id)
        self.__sumo_obs[ped_id][tc.VAR_ROAD_ID] = \
            self.kernel_api.person.getRoadID(ped_id)

        new_obs = self.kernel_api.person.getSubscriptionResults(ped_id)
        return new_obs

    def remove(self, ped_id):

        # remove from sumo
        if ped_id in self.kernel_api.person.getIDList():
            self.kernel_api.person.unsubscribe(ped_id)
            self.kernel_api.person.remove(ped_id)

        if ped_id in self.__ids:
            self.__ids.remove(ped_id)
        if ped_id in self.__sumo_obs:
            del self.__sumo_obs[ped_id]

    def get_speed(self, ped_id, error=-1001):
        if isinstance(ped_id, (list, np.ndarray)):
            return [self.get_speed(pedID, error) for pedID in ped_id]
        return self.__sumo_obs.get(ped_id, {}).get(tc.VAR_SPEED, error)

    def get_position(self, ped_id, error=-1001):
        if isinstance(ped_id, (list, np.ndarray)):
            return [self.get_position(pedID, error) for pedID in ped_id]
        return self.__sumo_obs.get(ped_id, {}).get(tc.VAR_POSITION, error)

    def get_edge(self, ped_id, error=-1001):
        if isinstance(ped_id, (list, np.ndarray)):
            return [self.get_edge(pedID, error) for pedID in ped_id]
        return self.__sumo_obs.get(ped_id, {}).get(tc.VAR_ROAD_ID, error)
