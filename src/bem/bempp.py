import bempp.api.linalg
from bempp.api.operators import potential, boundary
from bempp.api import GridFunction, export, function_space
import numpy as np
import warnings

# warnings.filterwarnings("ignore")
bempp.api.enable_console_logging("debug")
# bempp.api.BOUNDARY_OPERATOR_DEVICE_TYPE = "gpu"
# bempp.api.POTENTIAL_OPERATOR_DEVICE_TYPE = "gpu"


def obj_to_grid(vertices, elements):
    import bempp.api

    vertices = np.asarray(vertices)
    elements = np.asarray(elements)
    return bempp.api.Grid(vertices.T.astype(np.float64), elements.T.astype(np.uint32))


class BEMModel:
    def __init__(self, vertices, elements, wave_number, precision="single", fmm=False):
        """
        vertices: (n, 3) array
        elements: (m, 3) array
        """
        self.grid = obj_to_grid(vertices, elements)
        self.dp0_space = function_space(self.grid, "DP", 0)
        self.p1_space = function_space(self.grid, "P", 1)
        self.dirichlet_fun = None
        self.neumann_fun = None
        self.k = wave_number
        self.precision = precision
        self.fmm = fmm

    def get_dirichlet_coeff(self):
        return self.dirichlet_fun.coefficients

    def boundary_equation_solve(self, neumann_coeff):
        neumann_fun = GridFunction(
            self.dp0_space, coefficients=np.asarray(neumann_coeff)
        )
        self.neumann_fun = neumann_fun
        M = boundary.sparse.identity(
            self.p1_space,
            self.p1_space,
            self.p1_space,
            precision=self.precision,
            device_interface="opencl",
        )
        K = boundary.helmholtz.double_layer(
            self.p1_space,
            self.p1_space,
            self.p1_space,
            self.k,
            assembler="fmm" if self.fmm else "default_nonlocal",
            precision=self.precision,
            device_interface="opencl",
        )
        V = boundary.helmholtz.single_layer(
            self.dp0_space,
            self.p1_space,
            self.p1_space,
            self.k,
            assembler="fmm" if self.fmm else "default_nonlocal",
            precision=self.precision,
            device_interface="opencl",
        )
        left_side = -0.5 * M + K
        right_side = V * self.neumann_fun
        dirichlet_fun, info, res = bempp.api.linalg.gmres(
            left_side, right_side, tol=1e-6, maxiter=1000, return_residuals=True
        )
        self.dirichlet_fun = dirichlet_fun

    def potential_solve(self, points):
        """
        points: (*, 3) array
        """
        shape = points.shape
        points = points.reshape(-1, 3)
        potential_single = potential.helmholtz.single_layer(
            self.dp0_space,
            points.T,
            self.k,
            assembler="fmm" if self.fmm else "dense",
            precision=self.precision,
            device_interface="opencl",
        )
        potential_double = potential.helmholtz.double_layer(
            self.dp0_space,
            points.T,
            self.k,
            assembler="fmm" if self.fmm else "dense",
            precision=self.precision,
            device_interface="opencl",
        )
        dirichlet = (
            -potential_single * self.neumann_fun + potential_double * self.dirichlet_fun
        )
        return dirichlet.reshape(*shape[:-1])

    def export_neumann(self, filename):
        export(filename, grid_function=self.neumann_fun)

    def export_dirichlet(self, filename):
        export(filename, grid_function=self.dirichlet_fun)
