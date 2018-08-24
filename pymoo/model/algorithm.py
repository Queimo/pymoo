import copy
from abc import abstractmethod

from pymoo.model.evaluator import Evaluator
from pymoo.rand import random
from pymoo.util.non_dominated_rank import NonDominatedRank, find_non_dominated
from pymop.problem import Problem


class Algorithm:
    """

    This class represents the abstract class for any algorithm to be implemented. Most importantly it
    provides the solve method that is used to optimize a given problem.

    The solve method provides a wrapper function which does validate the input.

    """

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.disp = None
        self.func_display_attrs = None
        self.callback = None
        self.history = []

    def solve(self,
              problem,
              evaluator,
              seed=1,
              disp=False,
              callback=None,
              return_only_feasible=True,
              return_only_non_dominated=True,
              save_history=False,
              **kwargs
              ):
        """

        Solve a given problem by a given evaluator. The evaluator determines the termination condition and
        can either have a maximum budget, hypervolume or whatever. The problem can be any problem the algorithm
        is able to solve.

        Parameters
        ----------

        problem: class
            Problem to be solved by the algorithm

        evaluator: class
            object that evaluates and saves the number of evaluations and determines the stopping condition

        seed: int
            Random seed for this run. Before the algorithm starts this seed is set.

        disp : bool
            If it is true than information during the algorithm execution are displayed

        callback : func
            A callback function can be passed that is executed every generation. The parameters for the function
            are the algorithm itself, the number of evaluations so far and the current population.

                def callback(algorithm, n_evals, pop):
                    pass

        return_only_feasible : bool
            If true, only feasible solutions are returned.

        return_only_non_dominated : bool
            If true, only the non dominated solutions are returned. Otherwise, it might be - dependend on the
            algorithm - the final population

        save_history : bool
            If true, a current snapshot of each generation is saved.

        Returns
        -------
        X: matrix
            Design space

        F: matrix
            Objective space

        G: matrix
            Constraint space

        """

        # set the random seed for generator
        random.seed(seed)

        self.disp = disp
        self.callback = callback
        self.save_history = save_history

        # this allows to provide only an integer instead of an evaluator object
        if not isinstance(evaluator, Evaluator):
            evaluator = Evaluator(evaluator)

        # call the algorithm to solve the problem
        X, F, G = self._solve(problem, evaluator, **kwargs)

        if return_only_feasible:
            if G is not None and G.shape[0] == len(F) and G.shape[1] > 0:
                cv = Problem.calc_constraint_violation(G)[:, 0]
                X = X[cv <= 0, :]
                F = F[cv <= 0, :]
                if G is not None:
                    G = G[cv <= 0, :]

        if return_only_non_dominated:
            idx_non_dom = find_non_dominated(X)
            X = X[idx_non_dom, :]
            F = F[idx_non_dom, :]
            if G is not None:
                G = G[idx_non_dom, :]

        return X, F, G

    # method that is called each iteration to call some methods regularly
    def _each_iteration(self, D, first=False, **kwargs):

        # display the output if defined by the algorithm
        if self.disp and self.func_display_attrs is not None:
            disp = self.func_display_attrs(self.problem, self.evaluator, D)
            if disp is not None:
                self._display(disp, header=first)

        # if a callback function is provided it is called after each iteration
        if self.callback is not None:
            self.callback(D)

        if self.save_history:
            self.history.append(copy.deepcopy(D))

    # attributes are a list of tuples of length 3: (name, val, width)
    def _display(self, disp, header=False):
        regex = " | ".join(["{}"] * len(disp))
        if header:
            print("=" * 40)
            print(regex.format(*[name.ljust(width) for name, _, width in disp]))
            print("=" * 40)
        print(regex.format(*[str(val).ljust(width) for _, val, width in disp]))

    @abstractmethod
    def _solve(self, problem, evaluator):
        pass
