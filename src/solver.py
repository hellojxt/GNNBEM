import torch
import warnings
import time

# from https://gist.github.com/bridgesign/f421f69ad4a3858430e5e235bccde8c6


class BiCGSTAB:
    """
    This is a pytorch implementation of BiCGSTAB or BCGSTAB, a stable version
    of the CGD method, published first by Van Der Vrost.

    For solving ``Ax = b`` system.

    Example:

    solver = BiCGSTAB(Ax_gen)
    solver.solve(b, x=intial_x, tol=1e-10, atol=1e-16)

    """

    def __init__(self, Ax_gen, device="cuda"):
        """
        Ax_gen: A function that takes a 1-D tensor x and output Ax

        Note: This structure is follwed as it may not be computationally
        efficient to compute A explicitly.

        """
        self.Ax_gen = Ax_gen
        self.device = device

    def init_params(self, b, x=None, nsteps=None, tol=1e-10, atol=1e-16):
        """
        b: The R.H.S of the system. 1-D tensor
        nsteps: Number of steps of calculation
        tol: Tolerance such that if ||r||^2 < tol * ||b||^2 then converged
        atol:  Tolernace such that if ||r||^2 < atol then converged

        """
        self.b = b.clone().detach()
        self.x = torch.zeros_like(b) if x is None else x
        self.residual_tol = tol * torch.vdot(self.b, self.b).real
        self.atol = torch.tensor(atol, device=self.device)
        self.nsteps = b.shape[0] if nsteps is None else nsteps
        self.status, self.r = self.check_convergence(self.x)
        self.rho = torch.tensor(1, device=self.device)
        self.alpha = torch.tensor(1, device=self.device)
        self.omega = torch.tensor(1, device=self.device)
        self.v = torch.zeros(b.shape[0], device=self.device)
        self.p = torch.zeros(b.shape[0], device=self.device)
        self.r_hat = self.r.clone().detach()

    def check_convergence(self, x):
        r = self.b - self.Ax_gen(x)
        rdotr = torch.vdot(r, r).real
        if rdotr < self.residual_tol or rdotr < self.atol:
            return True, r
        else:
            return False, r

    def step(self):
        rho = torch.dot(self.r, self.r_hat)  # rho_i <- <r0, r^>
        beta = (rho / self.rho) * (
            self.alpha / self.omega
        )  # beta <- (rho_i/rho_{i-1}) x (alpha/omega_{i-1})
        self.rho = rho  # rho_{i-1} <- rho_i  replaced self value
        self.p = self.r + beta * (
            self.p - self.omega * self.v
        )  # p_i <- r_{i-1} + beta x (p_{i-1} - w_{i-1} v_{i-1}) replaced p self value
        self.v = self.Ax_gen(self.p)  # v_i <- Ap_i
        self.alpha = self.rho / torch.dot(
            self.r_hat, self.v
        )  # alpha <- rho_i/<r^, v_i>
        s = self.r - self.alpha * self.v  # s <- r_{i-1} - alpha v_i
        t = self.Ax_gen(s)  # t <- As
        self.omega = torch.dot(t, s) / torch.dot(t, t)  # w_i <- <t, s>/<t, t>
        self.x = (
            self.x + self.alpha * self.p + self.omega * s
        )  # x_i <- x_{i-1} + alpha p + w_i s
        status, res = self.check_convergence(self.x)
        if status:
            return True
        else:
            self.r = s - self.omega * t  # r_i <- s - w_i t
            return False

    def solve(self, *args, **kwargs):
        """
        Method to find the solution.

        Returns the final answer of x

        """
        self.init_params(*args, **kwargs)
        if self.status:
            return self.x
        iter_count = 0
        while self.nsteps:
            s = self.step()
            # print(self.x)
            iter_count += 1
            if s:
                print(f"Converged in {iter_count} steps")
                return self.x
            if self.rho == 0:
                break
            self.nsteps -= 1
        warnings.warn("Convergence has failed :(")
        return self.x


class BiCGSTAB_batch:
    def __init__(self, Ax_gen, device="cuda"):
        self.Ax_gen = Ax_gen
        self.device = device

    def init_params(self, b, x=None, nsteps=None, tol=1e-10, atol=1e-16):
        # b: The R.H.S of the system. of shape (n, 1, batch_size)
        batch_size = b.shape[2]
        n = b.shape[0]
        self.b = b.clone().detach()
        self.x = torch.zeros_like(b) if x is None else x
        self.residual_tol = tol * self.batch_vdot(self.b, self.b)
        self.atol = torch.tensor(atol, device=self.device)
        self.nsteps = n if nsteps is None else nsteps
        self.status, self.r = self.check_convergence(self.x)
        self.rho = torch.ones(1, 1, batch_size, device=self.device, dtype=b.dtype)
        self.alpha = torch.ones(1, 1, batch_size, device=self.device, dtype=b.dtype)
        self.omega = torch.ones(1, 1, batch_size, device=self.device, dtype=b.dtype)
        self.v = torch.zeros(n, 1, batch_size, device=self.device, dtype=b.dtype)
        self.p = torch.zeros(n, 1, batch_size, device=self.device, dtype=b.dtype)
        self.r_hat = self.r.clone().detach()

    def check_convergence(self, x):
        r = self.b - self.Ax_gen(x)
        rdotr = self.batch_vdot(r, r)
        self.rdotr = rdotr
        if (rdotr < self.residual_tol).all() or (rdotr < self.atol).all():
            return True, r
        else:
            return False, r

    def batch_vdot(self, x, y):
        return torch.linalg.vecdot(x, y, dim=0).real

    def batch_dot(self, x, y):
        return torch.linalg.vecdot(torch.conj(x), y, dim=0).unsqueeze(0)

    def step(self):
        rho = self.batch_dot(self.r, self.r_hat)  # rho_i <- <r0, r^>
        # print(rho.shape, self.rho.shape, self.alpha.shape, self.omega.shape)
        beta = (rho / self.rho) * (
            self.alpha / self.omega
        )  # beta <- (rho_i/rho_{i-1}) x (alpha/omega_{i-1})
        self.rho = rho  # rho_{i-1} <- rho_i  replaced self value
        # print(self.r.shape, beta.shape, self.p.shape, self.omega.shape, self.v.shape)
        self.p = self.r + beta * (
            self.p - self.omega * self.v
        )  # p_i <- r_{i-1} + beta x (p_{i-1} - w_{i-1} v_{i-1}) replaced p self value
        self.v = self.Ax_gen(self.p)  # v_i <- Ap_i
        self.alpha = self.rho / self.batch_dot(
            self.r_hat, self.v
        )  # alpha <- rho_i/<r^, v_i>
        s = self.r - self.alpha * self.v  # s <- r_{i-1} - alpha v_i
        t = self.Ax_gen(s)  # t <- As
        self.omega = self.batch_dot(t, s) / self.batch_dot(t, t)
        tmp_x = self.x + self.alpha * self.p + self.omega * s
        mask = torch.isnan(tmp_x) == False
        self.x[mask] = tmp_x[mask]  # x_i <- x_{i-1} + alpha p + w_i s
        status, res = self.check_convergence(self.x)
        if status:
            return True
        else:
            self.r = s - self.omega * t  # r_i <- s - w_i t
            return False

    def solve(self, *args, **kwargs):
        """
        Method to find the solution.

        Returns the final answer of x

        """
        self.init_params(*args, **kwargs)
        if self.status:
            return self.x
        iter_count = 0
        while self.nsteps:
            s = self.step()
            # print("step", iter_count, "with residual", self.rdotr)
            iter_count += 1
            if s:
                # print(f"Converged in {iter_count} steps")
                return self.x
            if (self.rho == 0).all():
                break
            self.nsteps -= 1
        print("Convergence has failed :(")
        return self.x


class BiCGSTAB_batch2:
    def __init__(self, Ax_gen, device="cuda"):
        self.Ax_gen = Ax_gen
        self.device = device

    def init_params(self, b, x=None, nsteps=None, tol=1e-10, atol=1e-16):
        # b: The R.H.S of the system. of shape (batch_size, n, 1)
        batch_size = b.shape[0]
        n = b.shape[1]
        self.b = b.clone().detach()
        self.x = torch.zeros_like(b) if x is None else x
        self.residual_tol = tol * self.batch_vdot(self.b, self.b)
        self.atol = torch.tensor(atol, device=self.device)
        self.nsteps = n if nsteps is None else nsteps
        self.status, self.r = self.check_convergence(self.x)
        self.rho = torch.ones(batch_size, 1, 1, device=self.device, dtype=b.dtype)
        self.alpha = torch.ones(batch_size, 1, 1, device=self.device, dtype=b.dtype)
        self.omega = torch.ones(batch_size, 1, 1, device=self.device, dtype=b.dtype)
        self.v = torch.zeros(batch_size, n, 1, device=self.device, dtype=b.dtype)
        self.p = torch.zeros(batch_size, n, 1, device=self.device, dtype=b.dtype)
        self.r_hat = self.r.clone().detach()

    def check_convergence(self, x):
        r = self.b - self.Ax_gen(x)
        rdotr = self.batch_vdot(r, r)
        if (rdotr < self.residual_tol).all() or (rdotr < self.atol).all():
            return True, r
        else:
            return False, r

    def batch_vdot(self, x, y):
        return torch.linalg.vecdot(x, y, dim=1).real

    def batch_dot(self, x, y):
        return torch.linalg.vecdot(torch.conj(x), y, dim=1).unsqueeze(1)

    def step(self):
        rho = self.batch_dot(self.r, self.r_hat)  # rho_i <- <r0, r^>
        # print(rho.shape, self.rho.shape, self.alpha.shape, self.omega.shape)
        beta = (rho / self.rho) * (
            self.alpha / self.omega
        )  # beta <- (rho_i/rho_{i-1}) x (alpha/omega_{i-1})
        self.rho = rho  # rho_{i-1} <- rho_i  replaced self value
        # print(self.r.shape, beta.shape, self.p.shape, self.omega.shape, self.v.shape)
        self.p = self.r + beta * (
            self.p - self.omega * self.v
        )  # p_i <- r_{i-1} + beta x (p_{i-1} - w_{i-1} v_{i-1}) replaced p self value
        self.v = self.Ax_gen(self.p)  # v_i <- Ap_i
        self.alpha = self.rho / self.batch_dot(
            self.r_hat, self.v
        )  # alpha <- rho_i/<r^, v_i>
        s = self.r - self.alpha * self.v  # s <- r_{i-1} - alpha v_i
        t = self.Ax_gen(s)  # t <- As
        self.omega = self.batch_dot(t, s) / self.batch_dot(t, t)
        self.x = (
            self.x + self.alpha * self.p + self.omega * s
        )  # x_i <- x_{i-1} + alpha p + w_i s
        status, res = self.check_convergence(self.x)
        if status:
            return True
        else:
            self.r = s - self.omega * t  # r_i <- s - w_i t
            return False

    def solve(self, *args, **kwargs):
        """
        Method to find the solution.

        Returns the final answer of x

        """
        self.init_params(*args, **kwargs)
        if self.status:
            return self.x
        iter_count = 0
        while self.nsteps:
            s = self.step()
            print("step", iter_count, "with residual", self.rdotr)
            # print(self.x)
            iter_count += 1
            if s:
                print(f"Converged in {iter_count} steps")
                return self.x
            if (self.rho == 0).all():
                break
            self.nsteps -= 1
        print("Convergence has failed :(")
        return self.x
