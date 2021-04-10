import numpy as np
from pointmass import PointMass
from scipy.constants import gravitational_constant


class StaticSystem:
    """a gravitational system containing several bodies

    Attributes
    ----------
    bodyindex: dict
        a dictionary that stores the index of each body in the arrays
        all_positions, all_velocitys, all_masses, so it is easy to
        track which column belongs to which body.
    all_positions: np.ndarray
        an array that stores all position arrays in a single array:
            body1.position = np.array([1, 2, 3])
            body2.position = np.array([4, 5, 6])
            MassSystem(body1, body2).all_positions == \
                np.array([[1, 2, 3], [4, 5, 6]])
    all_velocitys: np.ndarray
        an array that stores all velocity arrays in a single array
    all_masses: np.ndarray
        an array that stores all masses

    Methods
    -------
    step(inplace)
        run the simulation one timestep
    centre_of_mass()
        calculate the centre of mass of the mass-system
    fix()
        define the velocity of the centre of mass as zero and adjust
        all single velocities accordingly
    get_object(name)
        return the PointMass object named name
    """

    def __init__(self, not_yet_initialized=True, *args):
        """
        Parameters
        ----------
        not_yet_initialized: bool
            True if a new MassSysem is initialized from PointMass
            objects. False if all attributes are already in their
            final shape (this is for example used by step, if
            inplace=False)
        args:
            if not_yet_initialized is True: PointMass
            if not_yet_initialized is False:
                (np.ndarray, np.ndarray, np.ndarray, dict)
        """
        if not_yet_initialized:
            self.bodyindex = {}
            for i, body in enumerate(args):
                if body.name in self.bodyindex:
                    raise AttributeError("there are several objects called "
                                         + body.name)
                else:
                    self.bodyindex[body.name] = i

            shape = (len(args), len(args[0].position))

            self.all_positions = np.zeros(shape)
            for i, body in enumerate(args):
                self.all_positions[i] = body.position

            self.all_velocities = np.zeros(shape)
            for i, body in enumerate(args):
                self.all_velocities[i] = body.velocity

            self.all_masses = np.zeros(len(args))
            for i, body in enumerate(args):
                self.all_masses[i] = body.mass

        else:
            # this constructor is used by some methods
            self.all_positions = args[0]
            self.all_velocities = args[1]
            self.all_masses = args[2]
            self.bodyindex = args[3]

    def step(self, dt, grav_const=gravitational_constant, inplace=True):
        """calculate the next state of the gravitational system

        Parameters
        ----------
        dt: float
            The timestep on which the simulation operates
        grav_const: float, optional
            The gravitational constant. Default is the newtonian
            gravitational constant.
        inplace: bool, optional
            If inplace is True, the existing StaticSystem object
            gets modified
            If inplace is False, a new StaticSystem instance is
            returned
            Default is True.

        Returns
        -------
        StaticSystem, if inplace is False
            The state of the system after dt has elapsed
        """
        # calculate connection vector map
        shape = self.all_positions.shape
        gridshape = (shape[0], shape[0], shape[1])
        horizontal_grid = np.full(gridshape, self.all_positions)
        vertical_grid = horizontal_grid.transpose((1, 0, 2))
        convec_map = vertical_grid - horizontal_grid

        # calculate distance map (and reshape for further computation)
        dist_map = np.sqrt((convec_map ** 2).sum(axis=2))
        dist_map_rs = dist_map.reshape((shape[0], shape[0], 1))
        # replace 0s wit 1s to avoid division by zero (does not affect result)
        dist_map_rs[dist_map_rs == 0] = 1

        # calculate acceleration
        mlen = len(self.all_masses)
        mass_matrix = np.full((mlen, mlen), self.all_masses)
        mass_matrix = mass_matrix.reshape((mlen, mlen, 1))
        mx = convec_map * mass_matrix / (dist_map_rs ** 3)  # div by zero
        accelleration = - grav_const * mx.sum(axis=1)

        # update position and velocity
        if inplace:
            self.all_positions = self.all_positions + self.all_velocities * dt
            self.all_velocities = self.all_velocities + accelleration * dt
        else:
            all_positions = self.all_positions + self.all_velocities * dt
            all_velocities = self.all_velocities + accelleration * dt
            new_system = StaticSystem(all_positions,
                                      all_velocities,
                                      self.all_masses,
                                      self.bodyindex)
            return new_system

    def centre_of_mass(self):
        """calculate the centre of mass

        Returns
        -------
        np.ndarray
            The centre of mass
        """
        total_mass = self.all_masses.sum()
        mx = (self.all_positions * self.all_masses[:, None]).sum(axis=0)
        centreofmass = mx / total_mass
        return centreofmass

    def fix(self):
        """define the velocity of the centre of mass as zero and
        adjust self.all_velocities accordingly"""

        all_pulses = self.all_velocities * self.all_masses[:, None]
        total_pulse = all_pulses.sum(axis=0)
        total_mass = self.all_masses.sum()
        velocity_centre_of_mass = total_pulse / total_mass
        self.all_velocities = self.all_velocities - velocity_centre_of_mass

    def get_body(self, name: str):
        """return a PointMass object of the body named name

        Parameters
        ----------
        name: str
            the name of the object to return

        Returns
        -------
        PointMass
            the current state of the PointMass object
        """
        index = self.bodyindex(name)
        body = PointMass(name=name,
                         mass=self.all_masses[index],
                         position=self.all_positions[index],
                         velocity=self.all_velocities[index])
        return body
