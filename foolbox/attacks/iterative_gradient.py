import numpy as np
from collections import Iterable
import abc
import logging

from .base import Attack
from .base import generator_decorator


class IterativeGradientBaseAttack(Attack):
    """Common base class for iterative gradient attacks."""

    @abc.abstractmethod
    def _gradient(self, a, x):
        raise NotImplementedError

    def _run(self, a, epsilons, max_epsilon, steps):
        logging.warning(
            "Please consider using the L2BasicIterativeAttack,"
            " the LinfinityBasicIterativeAttack or one of its"
            " other variants such as the ProjectedGradientDescent"
            " attack."
        )
        if not a.has_gradient():
            logging.fatal(
                "Applied gradient-based attack to model that "
                "does not provide gradients."
            )
            return

        x = a.unperturbed
        min_, max_ = a.bounds()

        if not isinstance(epsilons, Iterable):
            assert isinstance(epsilons, int)
            max_epsilon_iter = max_epsilon / steps
            epsilons = np.linspace(0, max_epsilon_iter, num=epsilons + 1)[1:]

        for epsilon in epsilons:
            perturbed = x

            for _ in range(steps):
                for tmp in self._gradient(a, perturbed):
                    gradient = tmp
                #gradient = yield from self._gradient(a, perturbed)

                perturbed = perturbed + gradient * epsilon
                perturbed = np.clip(perturbed, min_, max_)

                for tmp in a.forward_one(perturbed):
                    tmp
                #yield from a.forward_one(perturbed)
                # we don't return early if an adversarial was found
                # because there might be a different epsilon
                # and/or step that results in a better adversarial


class IterativeGradientAttack(IterativeGradientBaseAttack):
    """Like GradientAttack but with several steps for each epsilon.

    """

    @generator_decorator
    def as_generator(self, a, epsilons=100, max_epsilon=1, steps=10):

        """Like GradientAttack but with several steps for each epsilon.

        Parameters
        ----------
        input_or_adv : `numpy.ndarray` or :class:`Adversarial`
            The original, unperturbed input as a `numpy.ndarray` or
            an :class:`Adversarial` instance.
        label : int
            The reference label of the original input. Must be passed
            if `a` is a `numpy.ndarray`, must not be passed if `a` is
            an :class:`Adversarial` instance.
        unpack : bool
            If true, returns the adversarial input, otherwise returns
            the Adversarial object.
        epsilons : int or Iterable[float]
            Either Iterable of step sizes in the gradient direction
            or number of step sizes between 0 and max_epsilon that should
            be tried.
        max_epsilon : float
            Largest step size if epsilons is not an iterable.
        steps : int
            Number of iterations to run.

        """

        for tmp in self._run(a, epsilons=epsilons, max_epsilon=max_epsilon, steps=steps):
            tmp
        #yield from self._run(a, epsilons=epsilons, max_epsilon=max_epsilon, steps=steps)

    def _gradient(self, a, x):
        min_, max_ = a.bounds()
        for tmp in a.gradient_one(x):
            gradient = tmp
        #gradient = yield from a.gradient_one(x)
        gradient_norm = np.sqrt(np.mean(np.square(gradient)))
        gradient = gradient / (gradient_norm + 1e-8) * (max_ - min_)
        return gradient


class IterativeGradientSignAttack(IterativeGradientBaseAttack):
    """Like GradientSignAttack but with several steps for each epsilon.

    """

    @generator_decorator
    def as_generator(self, a, epsilons=100, max_epsilon=1, steps=10):

        """Like GradientSignAttack but with several steps for each epsilon.

        Parameters
        ----------
        input_or_adv : `numpy.ndarray` or :class:`Adversarial`
            The original, unperturbed input as a `numpy.ndarray` or
            an :class:`Adversarial` instance.
        label : int
            The reference label of the original input. Must be passed
            if `a` is a `numpy.ndarray`, must not be passed if `a` is
            an :class:`Adversarial` instance.
        unpack : bool
            If true, returns the adversarial input, otherwise returns
            the Adversarial object.
        epsilons : int or Iterable[float]
            Either Iterable of step sizes in the direction of the sign of
            the gradient or number of step sizes between 0 and max_epsilon
            that should be tried.
        max_epsilon : float
            Largest step size if epsilons is not an iterable.
        steps : int
            Number of iterations to run.

        """

        yield from self._run(a, epsilons=epsilons, max_epsilon=max_epsilon, steps=steps)

    def _gradient(self, a, x):
        min_, max_ = a.bounds()
        gradient = yield from a.gradient_one(x)
        gradient = np.sign(gradient) * (max_ - min_)
        return gradient
